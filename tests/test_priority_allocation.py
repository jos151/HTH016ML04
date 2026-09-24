"""
Test Suite for SKU-level and Priority Allocation (Stage 8).
Validates multi-item rationing, priority weighting, and per-SKU inventory conservation.
"""
import pandas as pd
import pytest
from backend.allocation import allocate_sku_inventory


@pytest.fixture
def sample_multi_sku_forecast():
    """Provides a deterministic 2-store, 2-SKU forecast DataFrame."""
    return pd.DataFrame([
        {"store_id": "STORE_1", "sku_id": "SKU_01", "predicted_units": 100.0, "forecast_date": "2023-01-01"},
        {"store_id": "STORE_2", "sku_id": "SKU_01", "predicted_units": 100.0, "forecast_date": "2023-01-01"},
        {"store_id": "STORE_1", "sku_id": "SKU_02", "predicted_units": 50.0, "forecast_date": "2023-01-01"},
        {"store_id": "STORE_2", "sku_id": "SKU_02", "predicted_units": 50.0, "forecast_date": "2023-01-01"},
    ])


def test_sku_allocation_abundant_stock(sample_multi_sku_forecast):
    """Verify that when both SKUs have abundant stock, all demands are 100% fulfilled."""
    res = allocate_sku_inventory(
        forecast_df=sample_multi_sku_forecast,
        inventory_by_sku={"SKU_01": 300, "SKU_02": 200},
    )
    assert len(res) == 4
    assert (res["shortage"] == 0).all()
    assert (res["fulfillment_percentage"] == 100.0).all()


def test_sku_allocation_scarce_stock(sample_multi_sku_forecast):
    """Verify that rationing for one SKU does not cross-allocate or rob another SKU's stock."""
    # SKU_01 has 100 units (demand is 200) -> 50% fulfillment
    # SKU_02 has 100 units (demand is 100) -> 100% fulfillment
    res = allocate_sku_inventory(
        forecast_df=sample_multi_sku_forecast,
        inventory_by_sku={"SKU_01": 100, "SKU_02": 100},
    )
    sku1 = res[res["sku_id"] == "SKU_01"]
    sku2 = res[res["sku_id"] == "SKU_02"]

    assert sku1["allocated_units"].sum() == 100
    assert sku1["shortage"].sum() == 100

    assert sku2["allocated_units"].sum() == 100
    assert sku2["shortage"].sum() == 0


def test_sku_allocation_zero_stock_for_one_sku(sample_multi_sku_forecast):
    """Verify that a zero-stock SKU gets zero allocation while stocked SKU is fulfilled."""
    res = allocate_sku_inventory(
        forecast_df=sample_multi_sku_forecast,
        inventory_by_sku={"SKU_01": 0, "SKU_02": 100},
    )
    sku1 = res[res["sku_id"] == "SKU_01"]
    sku2 = res[res["sku_id"] == "SKU_02"]

    assert (sku1["allocated_units"] == 0).all()
    assert sku1["shortage"].sum() == 200
    assert sku2["allocated_units"].sum() == 100


def test_store_priority_weighting(sample_multi_sku_forecast):
    """Verify that higher store priority receives preferential quota under scarcity."""
    # SKU_01 demand: STORE_1=100, STORE_2=100. Available=100.
    # If STORE_1 has weight 2.0 and STORE_2 has weight 1.0, STORE_1 gets ~67 units, STORE_2 gets ~33 units.
    res = allocate_sku_inventory(
        forecast_df=sample_multi_sku_forecast,
        inventory_by_sku={"SKU_01": 100, "SKU_02": 50},
        store_priorities={"STORE_1": 2.0, "STORE_2": 1.0},
    )
    sku1 = res[res["sku_id"] == "SKU_01"]
    s1_alloc = sku1[sku1["store_id"] == "STORE_1"]["allocated_units"].iloc[0]
    s2_alloc = sku1[sku1["store_id"] == "STORE_2"]["allocated_units"].iloc[0]

    assert s1_alloc > s2_alloc
    assert s1_alloc + s2_alloc == 100


def test_lp_method_in_sku_allocation(sample_multi_sku_forecast):
    """Verify that allocate_sku_inventory works with allocation_method='lp'."""
    res = allocate_sku_inventory(
        forecast_df=sample_multi_sku_forecast,
        inventory_by_sku={"SKU_01": 120, "SKU_02": 80},
        allocation_method="lp",
    )
    assert not res.empty
    assert res["allocated_units"].sum() == 200
    assert (res["allocated_units"] >= 0).all()


def test_empty_forecast_sku_allocation():
    """Verify empty input DataFrame returns structured empty output."""
    empty_df = pd.DataFrame(columns=["store_id", "sku_id", "predicted_units"])
    res = allocate_sku_inventory(empty_df, total_available_units=100)
    assert res.empty
    assert "warehouse_id" in res.columns
