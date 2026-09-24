"""
Test Suite for Scenario Simulation and Comparative Analysis (Stage 10).
"""
import pandas as pd
import pytest
from backend.forecasting import forecast_demand
from backend.allocation import allocate_inventory


@pytest.fixture
def base_history():
    dates = pd.date_range("2023-01-01", periods=14, freq="D")
    records = []
    for d in dates:
        for s in ["STORE_1", "STORE_2"]:
            for k in ["SKU_01"]:
                records.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "store_id": s,
                    "sku_id": k,
                    "units_sold": 20.0,
                })
    return pd.DataFrame(records)


def test_baseline_vs_promotion_scenario(base_history):
    """Verify promotion scenario increases demand only for targeted store."""
    fc_base = forecast_demand(base_history, horizon_days=7)
    fc_promo = forecast_demand(base_history, horizon_days=7, promo_boost={"STORE_1": 1.30})

    s1_base = fc_base[fc_base["store_id"] == "STORE_1"]["predicted_units"].sum()
    s1_promo = fc_promo[fc_promo["store_id"] == "STORE_1"]["predicted_units"].sum()

    s2_base = fc_base[fc_base["store_id"] == "STORE_2"]["predicted_units"].sum()
    s2_promo = fc_promo[fc_promo["store_id"] == "STORE_2"]["predicted_units"].sum()

    assert round(s1_promo / s1_base, 2) == 1.30
    assert s2_base == s2_promo


def test_baseline_vs_holiday_scenario(base_history):
    """Verify holiday mode scales all stores uniformly by 1.15."""
    fc_base = forecast_demand(base_history, horizon_days=7, is_holiday_week=False)
    fc_hol = forecast_demand(base_history, horizon_days=7, is_holiday_week=True)

    ratio = fc_hol["predicted_units"].sum() / fc_base["predicted_units"].sum()
    assert abs(ratio - 1.15) < 0.001


def test_allocation_recalculation_after_demand_shift(base_history):
    """Verify inventory shortage increases when promotional uplift expands demand against fixed inventory."""
    fc_base = forecast_demand(base_history, horizon_days=7)
    fc_promo = forecast_demand(base_history, horizon_days=7, promo_boost={"STORE_1": 1.50})

    alloc_base = allocate_inventory(fc_base, total_available_units=200)
    alloc_promo = allocate_inventory(fc_promo, total_available_units=200)

    # Both must allocate exactly 200 units (supply cap)
    assert alloc_base["allocated_units"].sum() == 200
    assert alloc_promo["allocated_units"].sum() == 200

    # Shortage in promo must be higher than base
    assert alloc_promo["shortage"].sum() > alloc_base["shortage"].sum()


def test_inventory_increase_scenario(base_history):
    """Verify doubling warehouse inventory eliminates shortage."""
    fc = forecast_demand(base_history, horizon_days=7)
    total_demand = fc["predicted_units"].sum()

    alloc_scarce = allocate_inventory(fc, total_available_units=int(total_demand * 0.5))
    alloc_abundant = allocate_inventory(fc, total_available_units=int(total_demand * 1.5))

    assert alloc_scarce["shortage"].sum() > 0
    assert alloc_abundant["shortage"].sum() == 0
