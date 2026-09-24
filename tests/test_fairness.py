"""
Test Suite for Allocation Fairness and Equity Indicators (Stage 12).
"""
import pandas as pd
import pytest
from backend.inventory_planning import calculate_allocation_fairness


def test_equal_fulfillment_fairness():
    """Verify that equal fulfillment percentage across stores yields fairness score ~ 1.0."""
    alloc_df = pd.DataFrame([
        {"store_id": "STORE_1", "forecasted_demand": 100.0, "allocated_units": 80.0},
        {"store_id": "STORE_2", "forecasted_demand": 200.0, "allocated_units": 160.0},
    ])
    res = calculate_allocation_fairness(alloc_df)
    assert res["min_fulfillment_pct"] == 80.0
    assert res["max_fulfillment_pct"] == 80.0
    assert res["spread_pct"] == 0.0
    assert res["fairness_score"] == 1.0
    assert len(res["underserved_stores"]) == 0


def test_unequal_fulfillment_detection():
    """Verify that disparate fulfillment spreads flag underserved stores."""
    alloc_df = pd.DataFrame([
        {"store_id": "STORE_1", "forecasted_demand": 100.0, "allocated_units": 95.0}, # 95%
        {"store_id": "STORE_2", "forecasted_demand": 100.0, "allocated_units": 40.0}, # 40%
    ])
    res = calculate_allocation_fairness(alloc_df)
    assert res["min_fulfillment_pct"] == 40.0
    assert res["max_fulfillment_pct"] == 95.0
    assert res["spread_pct"] == 55.0
    assert res["fairness_score"] < 1.0
    assert "STORE_2" in res["underserved_stores"]
    assert "STORE_1" in res["best_served_stores"]


def test_empty_dataframe_fairness():
    """Verify empty input returns structured default dictionary."""
    res = calculate_allocation_fairness(pd.DataFrame())
    assert res["fairness_score"] == 1.0
    assert res["spread_pct"] == 0.0
