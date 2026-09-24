"""
End-to-end integration and pipeline invariant test suite.
Validates the complete execution flow from dataset loading to forecasting,
to constrained inventory allocation, and finally to API responses.
"""

from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.data_loader import load_demand_data
from backend.forecasting import forecast_demand
from backend.allocation import allocate_inventory, allocate_inventory_lp
from backend.main import app

client = TestClient(app)


def test_complete_pipeline_flow_data_to_api():
    """1. Validates complete flow: data loading -> forecasting -> inventory allocation -> API response."""
    # Step 1: Ingestion
    raw_df = load_demand_data()
    assert not raw_df.empty
    assert set(["date", "store_id", "sku_id", "units_sold"]).issubset(raw_df.columns)

    # Step 2: Forecasting
    forecast_df = forecast_demand(raw_df, horizon_days=7)
    assert not forecast_df.empty
    assert set(["store_id", "sku_id", "forecast_date", "predicted_units"]).issubset(forecast_df.columns)

    # Step 3: Allocation
    supply = 1500.0
    alloc_df = allocate_inventory(forecast_df, total_available_units=supply)
    assert not alloc_df.empty
    assert set(["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]).issubset(alloc_df.columns)

    # Step 4: Compare with API response
    api_res = client.post("/allocate", json={
        "total_available_units": supply,
        "method": "proportional",
        "horizon_days": 7,
    })
    assert api_res.status_code == 200
    api_data = api_res.json()

    # Exact mathematical match between direct engine and API
    api_summary = api_data["summary"]
    engine_summary = alloc_df.attrs["summary"]
    assert api_summary["total_forecasted_demand"] == engine_summary["total_forecasted_demand"]
    assert api_summary["total_allocated_units"] == engine_summary["total_allocated_units"]
    assert api_summary["total_shortage"] == engine_summary["total_shortage"]


def test_store_and_sku_ids_survival():
    """2. Invariant: Store IDs survive all pipeline stages, and SKU IDs survive forecasting."""
    raw_df = load_demand_data()
    raw_stores = sorted(raw_df["store_id"].unique().tolist())
    raw_skus = sorted(raw_df["sku_id"].unique().tolist())

    # After forecasting
    forecast_df = forecast_demand(raw_df, horizon_days=7)
    fc_stores = sorted(forecast_df["store_id"].unique().tolist())
    fc_skus = sorted(forecast_df["sku_id"].unique().tolist())
    assert fc_stores == raw_stores, "Store IDs were lost or altered during forecasting"
    assert fc_skus == raw_skus, "SKU IDs were lost or altered during forecasting"

    # After allocation
    alloc_df = allocate_inventory(forecast_df, total_available_units=1000)
    alloc_stores = sorted(alloc_df["store_id"].unique().tolist())
    assert alloc_stores == raw_stores, "Store IDs were lost or altered during allocation"

    # In API response
    api_res = client.post("/allocate", json={"total_available_units": 1000, "method": "proportional"})
    api_stores = sorted([a["store_id"] for a in api_res.json()["allocations"]])
    assert api_stores == raw_stores, "Store IDs were lost in API allocation response"


def test_forecast_dates_correctness():
    """3. Invariant: Forecast dates strictly follow the max historical date in consecutive order."""
    raw_df = load_demand_data()
    max_hist_date = pd.to_datetime(raw_df["date"].max())

    horizon = 10
    forecast_df = forecast_demand(raw_df, horizon_days=horizon)
    unique_dates = sorted(forecast_df["forecast_date"].unique().tolist())

    expected_dates = [
        (max_hist_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, horizon + 1)
    ]
    assert unique_dates == expected_dates, "Forecast dates are not strictly consecutive from historical end date"


def test_predictions_non_negative():
    """4. Invariant: Predictions and baseline values are strictly non-negative across all entities."""
    raw_df = load_demand_data()
    for h in [1, 7, 14]:
        forecast_df = forecast_demand(raw_df, horizon_days=h)
        assert (forecast_df["predicted_units"] >= 0.0).all()
        assert (forecast_df["baseline_units"] >= 0.0).all()
        assert not forecast_df["predicted_units"].isnull().any()


def test_allocation_supply_and_demand_invariants():
    """5. Invariants: Total allocation <= supply, store allocation <= store demand, allocation + shortage == demand."""
    raw_df = load_demand_data()
    forecast_df = forecast_demand(raw_df, horizon_days=7)

    # Test under scarce, exact, and surplus supply
    tot_demand = forecast_df["predicted_units"].sum()
    for supply in [0, 50, int(tot_demand // 2), int(tot_demand), int(tot_demand * 1.5)]:
        alloc_df = allocate_inventory(forecast_df, total_available_units=supply)

        # Invariant A: Total allocation does not exceed inventory
        assert alloc_df["allocated_units"].sum() <= supply + 1e-6

        # Invariant B: No allocation exceeds demand
        assert (alloc_df["allocated_units"] <= alloc_df["forecasted_demand"]).all()

        # Invariant C: Shortage is internally consistent (allocated + shortage == demand)
        assert (alloc_df["allocated_units"] + alloc_df["shortage"] == alloc_df["forecasted_demand"]).all()

        # Invariant D: Excess is zero when allocation <= demand
        assert (alloc_df["excess"] == 0).all()


def test_promotion_and_holiday_invariants():
    """6. Invariants: Promotion affects only designated store; holiday affects all stores by 1.15x."""
    raw_df = load_demand_data()
    base_fc = forecast_demand(raw_df, horizon_days=7)

    # 1. Promotion isolation
    target_store = "STORE_2"
    promo_fc = forecast_demand(raw_df, horizon_days=7, promo_boost={target_store: 1.30})

    for s in raw_df["store_id"].unique():
        base_s = base_fc[base_fc["store_id"] == s]["predicted_units"].sum()
        promo_s = promo_fc[promo_fc["store_id"] == s]["predicted_units"].sum()
        if s == target_store:
            assert abs((promo_s / base_s) - 1.30) < 0.01, f"{s} promotion was not scaled by 1.30"
        else:
            assert base_s == promo_s, f"{s} should be completely unaffected by {target_store} promotion"

    # 2. Holiday universal scaling
    hol_fc = forecast_demand(raw_df, horizon_days=7, is_holiday_week=True)
    for s in raw_df["store_id"].unique():
        base_s = base_fc[base_fc["store_id"] == s]["predicted_units"].sum()
        hol_s = hol_fc[hol_fc["store_id"] == s]["predicted_units"].sum()
        assert abs((hol_s / base_s) - 1.15) < 0.01, f"{s} holiday was not scaled by 1.15"


def test_repeated_requests_determinism():
    """7. Invariant: Repeated invocations with identical parameters produce strictly deterministic results."""
    raw_df = load_demand_data()

    fc_1 = forecast_demand(raw_df, horizon_days=7, promo_boost={"STORE_1": 1.25}, is_holiday_week=True)
    fc_2 = forecast_demand(raw_df, horizon_days=7, promo_boost={"STORE_1": 1.25}, is_holiday_week=True)
    pd.testing.assert_frame_equal(fc_1, fc_2)

    al_1 = allocate_inventory(fc_1, total_available_units=1200)
    al_2 = allocate_inventory(fc_2, total_available_units=1200)
    pd.testing.assert_frame_equal(al_1, al_2)

    # Via API
    payload = {
        "total_available_units": 1200,
        "method": "proportional",
        "horizon_days": 7,
        "promo_boost": {"STORE_1": 1.25},
        "is_holiday_week": True,
    }
    api_1 = client.post("/allocate", json=payload).json()
    api_2 = client.post("/allocate", json=payload).json()
    assert api_1 == api_2


def test_fixtures_work_with_complete_pipeline():
    """8. Invariant: Synthetic test fixtures integrate seamlessly through the complete pipeline."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "data" / "test_fixtures"

    # Test shortage_case.csv through full pipeline
    shortage_path = fixtures_dir / "shortage_case.csv"
    f_df = load_demand_data(shortage_path)
    fc_df = forecast_demand(f_df, horizon_days=1)
    al_df = allocate_inventory(fc_df, total_available_units=1000)

    alloc_map = dict(zip(al_df["store_id"], al_df["allocated_units"]))
    assert alloc_map["STORE_A"] == 417
    assert alloc_map["STORE_B"] == 333
    assert alloc_map["STORE_C"] == 250
    assert al_df.attrs["summary"]["total_shortage"] == 200.0

    # Test rounding_case.csv through full pipeline
    rounding_path = fixtures_dir / "rounding_case.csv"
    r_df = load_demand_data(rounding_path)
    r_fc = forecast_demand(r_df, horizon_days=1)
    r_al = allocate_inventory(r_fc, total_available_units=2)
    assert r_al.attrs["summary"]["total_allocated_units"] == 2.0
    assert (r_al["allocated_units"] <= 1).all()

    # Test dominant_store_case.csv through full pipeline
    dominant_path = fixtures_dir / "dominant_store_case.csv"
    d_df = load_demand_data(dominant_path)
    d_fc = forecast_demand(d_df, horizon_days=1)
    d_al = allocate_inventory(d_fc, total_available_units=500)
    assert d_al.attrs["summary"]["total_allocated_units"] == 500.0
    assert (d_al["allocated_units"] >= 0).all()
