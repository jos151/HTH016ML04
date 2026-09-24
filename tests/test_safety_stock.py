"""
Test Suite for Safety Stock and Reorder Logic (Stage 11).
"""
import pandas as pd
import pytest
from backend.inventory_planning import calculate_safety_stock_and_reorder, get_z_score


@pytest.fixture
def history_df():
    dates = pd.date_range("2023-01-01", periods=14, freq="D")
    records = []
    for d in dates:
        records.append({
            "date": d.strftime("%Y-%m-%d"),
            "store_id": "STORE_1",
            "sku_id": "SKU_01",
            "units_sold": 10.0,
        })
    return pd.DataFrame(records)


def test_z_score_table():
    """Verify standard Z-scores for standard service levels."""
    assert abs(get_z_score(0.95) - 1.6449) < 0.001
    assert abs(get_z_score(0.90) - 1.2816) < 0.001
    assert abs(get_z_score(0.99) - 2.3263) < 0.001


def test_safety_stock_constant_demand(history_df):
    """Verify safety stock is 0 or minimum when demand standard deviation is 0."""
    res = calculate_safety_stock_and_reorder(
        historical_df=history_df,
        lead_time_days=7,
        target_service_level=0.95,
        current_inventory={"SKU_01": 50},
    )
    assert len(res) == 1
    row = res.iloc[0]
    # avg_daily is 10.0, lead_time is 7 -> LTD = 70.0
    assert row["avg_daily_demand"] == 10.0
    assert row["lead_time_demand"] == 70.0
    assert row["reorder_point"] >= row["lead_time_demand"]


def test_reorder_qty_moq_and_pack_size_rounding(history_df):
    """Verify recommended order quantity respects MOQ and rounds up to pack size."""
    # LTD=70, SS ~ 10 -> ROP ~ 80. Current stock = 20 -> Net shortfall ~ 60.
    # MOQ = 50, Pack size = 12. 60 rounded up to multiple of 12 is 60 or 72.
    res = calculate_safety_stock_and_reorder(
        historical_df=history_df,
        current_inventory={"SKU_01": 20},
        min_order_qty=50,
        pack_size=12,
    )
    order_qty = res.iloc[0]["suggested_order_qty"]
    assert order_qty >= 50
    assert order_qty % 12 == 0


def test_negative_lead_time_rejection(history_df):
    """Verify non-positive lead time raises ValueError."""
    with pytest.raises(ValueError, match="lead_time_days must be positive"):
        calculate_safety_stock_and_reorder(history_df, lead_time_days=-1)

    with pytest.raises(ValueError, match="lead_time_days must be positive"):
        calculate_safety_stock_and_reorder(history_df, lead_time_days=0)


def test_invalid_service_level_rejection(history_df):
    """Verify invalid service level raises ValueError."""
    with pytest.raises(ValueError, match="target_service_level"):
        calculate_safety_stock_and_reorder(history_df, target_service_level=1.5)

    with pytest.raises(ValueError, match="target_service_level"):
        calculate_safety_stock_and_reorder(history_df, target_service_level=0.1)
