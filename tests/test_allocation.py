"""
Unit tests for deterministic proportional inventory allocation in backend/allocation.py.
"""

import pandas as pd
import pytest
from backend.allocation import allocate_inventory, allocate_inventory_lp, get_allocation_summary


def test_mandatory_worked_example():
    """Mandatory test: Store A=500, Store B=400, Store C=300, Available=1000."""
    df_forecast = pd.DataFrame({
        "store_id": ["Store A", "Store B", "Store C"],
        "predicted_units": [500.0, 400.0, 300.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=1000)

    # Validate schema
    expected_cols = ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
    assert list(res.columns) == expected_cols

    # Check exact allocations per largest-remainder method
    a_alloc = res.loc[res["store_id"] == "Store A", "allocated_units"].iloc[0]
    b_alloc = res.loc[res["store_id"] == "Store B", "allocated_units"].iloc[0]
    c_alloc = res.loc[res["store_id"] == "Store C", "allocated_units"].iloc[0]

    assert a_alloc == 417
    assert b_alloc == 333
    assert c_alloc == 250

    # Check totals & shortage
    assert res["allocated_units"].sum() == 1000
    assert res["shortage"].sum() == 200

    summary = res.attrs["summary"]
    assert summary["total_forecasted_demand"] == 1200.0
    assert summary["total_available_units"] == 1000.0
    assert summary["total_allocated_units"] == 1000.0
    assert summary["total_shortage"] == 200.0
    assert summary["total_excess"] == 0.0
    assert summary["remaining_inventory"] == 0.0


def test_inventory_greater_than_demand():
    """Tests inventory surplus: every store receives 100% of demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [100.0, 200.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=500)
    assert res.loc[res["store_id"] == "STORE_1", "allocated_units"].iloc[0] == 100
    assert res.loc[res["store_id"] == "STORE_2", "allocated_units"].iloc[0] == 200
    assert res["shortage"].sum() == 0
    assert res["excess"].sum() == 0
    assert res.attrs["summary"]["remaining_inventory"] == 200.0


def test_inventory_equal_to_demand():
    """Tests exact balance: inventory equals total demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [150.0, 250.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=400)
    assert res["allocated_units"].tolist() == [150, 250]
    assert res["shortage"].sum() == 0
    assert res["excess"].sum() == 0
    assert res.attrs["summary"]["remaining_inventory"] == 0.0


def test_inventory_below_demand():
    """Tests scarcity: inventory is less than total demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [100.0, 100.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=50)
    assert res["allocated_units"].tolist() == [25, 25]
    assert res["allocated_units"].sum() == 50
    assert res["shortage"].sum() == 150


def test_zero_inventory():
    """Tests when available inventory is zero."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [50.0, 50.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=0)
    assert (res["allocated_units"] == 0).all()
    assert res["shortage"].tolist() == [50, 50]
    assert res["excess"].tolist() == [0, 0]


def test_zero_demand():
    """Tests when forecasted demand is zero."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [0.0, 0.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=100)
    assert (res["allocated_units"] == 0).all()
    assert (res["shortage"] == 0).all()
    assert (res["excess"] == 0).all()
    assert res.attrs["summary"]["remaining_inventory"] == 100.0


def test_negative_inventory_rejection():
    """Tests that negative available inventory raises ValueError."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1"],
        "predicted_units": [10.0],
    })
    with pytest.raises(ValueError, match="total_available_units must be non-negative"):
        allocate_inventory(df_forecast, total_available_units=-10)


def test_empty_input():
    """Tests handling of empty forecast dataframe."""
    empty_df = pd.DataFrame(columns=["store_id", "predicted_units"])
    res = allocate_inventory(empty_df, total_available_units=50)
    assert res.empty
    assert list(res.columns) == ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
    assert res.attrs["summary"]["total_allocated_units"] == 0.0


def test_integer_allocation_types():
    """Tests that allocations, shortages, and excesses are strictly whole integers."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2", "STORE_3"],
        "predicted_units": [33.3, 33.3, 33.4],
    })
    res = allocate_inventory(df_forecast, total_available_units=50)
    for col in ["forecasted_demand", "allocated_units", "shortage", "excess"]:
        assert pd.api.types.is_integer_dtype(res[col])


def test_rounding_three_stores_one_unit_each_two_available():
    """Tests edge case: 3 stores demanding 1 unit each, with 2 available."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_A", "STORE_B", "STORE_C"],
        "predicted_units": [1.0, 1.0, 1.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=2)
    assert res["allocated_units"].sum() == 2
    assert (res["allocated_units"] <= 1).all()
    assert res["shortage"].sum() == 1


def test_allocation_never_exceeds_inventory():
    """Invariant test: Total allocated units <= available units."""
    df_forecast = pd.DataFrame({
        "store_id": [f"STORE_{i}" for i in range(10)],
        "predicted_units": [25.0] * 10,
    })
    for supply in [1, 7, 53, 100, 249, 250, 300]:
        res = allocate_inventory(df_forecast, total_available_units=supply)
        assert res["allocated_units"].sum() <= supply


def test_allocation_never_exceeds_demand():
    """Invariant test: No store receives more than its demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [10.0, 20.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=1000)
    assert (res["allocated_units"] <= res["forecasted_demand"]).all()


def test_allocation_plus_shortage_equals_demand():
    """Invariant test: allocated_units + shortage == forecasted_demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2", "STORE_3"],
        "predicted_units": [45.0, 80.0, 125.0],
    })
    res = allocate_inventory(df_forecast, total_available_units=150)
    assert (res["allocated_units"] + res["shortage"] == res["forecasted_demand"]).all()


def test_deterministic_repeatability():
    """Tests that repeated calls with identical input produce identical output."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_B", "STORE_A", "STORE_C"],
        "predicted_units": [400.0, 500.0, 300.0],
    })
    res1 = allocate_inventory(df_forecast, total_available_units=1000)
    res2 = allocate_inventory(df_forecast, total_available_units=1000)
    pd.testing.assert_frame_equal(res1, res2)


def test_large_values():
    """Tests scalability with large demand and large inventory."""
    df_forecast = pd.DataFrame({
        "store_id": [f"STORE_{i}" for i in range(50)],
        "predicted_units": [10000.0] * 50,
    })
    res = allocate_inventory(df_forecast, total_available_units=333333)
    assert res["allocated_units"].sum() == 333333
    assert (res["allocated_units"] <= 10000).all()


# ==============================================================================
# Linear Programming Allocation Tests (PuLP)
# ==============================================================================

def test_lp_sufficient_inventory():
    """LP Test: When inventory exceeds demand, all stores receive 100% of demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [100.0, 200.0],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=500)
    assert res.loc[res["store_id"] == "STORE_1", "allocated_units"].iloc[0] == 100
    assert res.loc[res["store_id"] == "STORE_2", "allocated_units"].iloc[0] == 200
    assert res["shortage"].sum() == 0
    assert res["excess"].sum() == 0
    assert res.attrs["summary"]["remaining_inventory"] == 200.0


def test_lp_insufficient_inventory():
    """LP Test: When inventory is scarce, total allocation equals available supply."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [100.0, 100.0],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=50)
    assert res["allocated_units"].sum() == 50
    assert res["shortage"].sum() == 150
    assert (res["allocated_units"] <= res["forecasted_demand"]).all()


def test_lp_zero_inventory():
    """LP Test: When available inventory is zero, all allocations are 0 and shortage == demand."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [50.0, 70.0],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=0)
    assert (res["allocated_units"] == 0).all()
    assert res["shortage"].tolist() == [50, 70]
    assert res["excess"].tolist() == [0, 0]


def test_lp_zero_demand():
    """LP Test: When forecasted demand is zero, all allocations are zero without error."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2"],
        "predicted_units": [0.0, 0.0],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=100)
    assert (res["allocated_units"] == 0).all()
    assert (res["shortage"] == 0).all()
    assert (res["excess"] == 0).all()
    assert res.attrs["summary"]["remaining_inventory"] == 100.0


def test_lp_integer_output():
    """LP Test: Integer units constraint: allocations, shortages, and excesses are strictly whole integers."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2", "STORE_3"],
        "predicted_units": [33.3, 33.3, 33.4],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=50)
    for col in ["forecasted_demand", "allocated_units", "shortage", "excess"]:
        assert pd.api.types.is_integer_dtype(res[col])
    assert res["allocated_units"].sum() == 50


def test_lp_inventory_constraint():
    """LP Invariant: Total allocated units never exceeds available units."""
    df_forecast = pd.DataFrame({
        "store_id": [f"STORE_{i}" for i in range(5)],
        "predicted_units": [50.0] * 5,
    })
    for supply in [0, 10, 75, 249, 250, 300]:
        res = allocate_inventory_lp(df_forecast, total_available_units=supply)
        assert res["allocated_units"].sum() <= supply


def test_lp_demand_reconciliation():
    """LP Invariant: For all stores, allocated_units + shortage == forecasted_demand (under no overstock)."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1", "STORE_2", "STORE_3"],
        "predicted_units": [45.0, 80.0, 125.0],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=150)
    assert (res["allocated_units"] + res["shortage"] == res["forecasted_demand"]).all()
    assert (res["excess"] == 0).all()


def test_lp_no_overstock_by_default():
    """LP Test: Stores never receive more than their demand by default even under excess supply."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_A", "STORE_B"],
        "predicted_units": [20.0, 30.0],
    })
    res = allocate_inventory_lp(df_forecast, total_available_units=1000, allow_overstock=False)
    assert (res["allocated_units"] <= res["forecasted_demand"]).all()
    assert (res["excess"] == 0).all()
    assert res["allocated_units"].sum() == 50


def test_lp_solver_failure_handling(monkeypatch):
    """LP Test: Solver failure handling: raises RuntimeError or falls back with warning when configured."""
    df_forecast = pd.DataFrame({
        "store_id": ["STORE_1"],
        "predicted_units": [10.0],
    })

    def mock_solve_fail(*args, **kwargs):
        raise RuntimeError("Mock solver crashed")

    monkeypatch.setattr("pulp.LpProblem.solve", mock_solve_fail)

    # 1. Without fallback -> raises RuntimeError
    with pytest.raises(RuntimeError, match="Linear programming allocation failed"):
        allocate_inventory_lp(df_forecast, total_available_units=10, fallback_on_solver_error=False)

    # 2. With fallback -> falls back to proportional allocation
    with pytest.warns(UserWarning, match="Falling back to proportional allocation"):
        fb_res = allocate_inventory_lp(df_forecast, total_available_units=10, fallback_on_solver_error=True)
        assert fb_res.attrs.get("solver_fallback") is True
        assert fb_res.loc[fb_res["store_id"] == "STORE_1", "allocated_units"].iloc[0] == 10

