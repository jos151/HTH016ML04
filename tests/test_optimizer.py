"""
Test Suite for Linear Programming (PuLP MILP) Optimization (Stage 9).
"""
import pandas as pd
import pytest
from backend.allocation import allocate_inventory_lp


@pytest.fixture
def standard_forecast():
    return pd.DataFrame([
        {"store_id": "STORE_A", "predicted_units": 500.0},
        {"store_id": "STORE_B", "predicted_units": 400.0},
        {"store_id": "STORE_C", "predicted_units": 300.0},
    ])


def test_lp_solver_availability():
    """Verify that PuLP CBC solver is available and returns an executable path."""
    import pulp
    solver = pulp.PULP_CBC_CMD(msg=False)
    assert bool(solver.available()) is True


def test_lp_sufficient_inventory(standard_forecast):
    """Verify full allocation when inventory exceeds demand."""
    res = allocate_inventory_lp(standard_forecast, total_available_units=1500)
    assert res["allocated_units"].sum() == 1200
    assert res["shortage"].sum() == 0
    assert (res["allocated_units"] == res["forecasted_demand"]).all()


def test_lp_scarce_inventory(standard_forecast):
    """Verify allocation respects capacity under shortage."""
    res = allocate_inventory_lp(standard_forecast, total_available_units=1000)
    assert res["allocated_units"].sum() == 1000
    assert res["shortage"].sum() == 200
    assert (res["allocated_units"] <= res["forecasted_demand"]).all()


def test_lp_zero_inventory(standard_forecast):
    """Verify 0 inventory produces 0 allocation and full shortage."""
    res = allocate_inventory_lp(standard_forecast, total_available_units=0)
    assert (res["allocated_units"] == 0).all()
    assert res["shortage"].sum() == 1200


def test_lp_zero_demand():
    """Verify zero demand produces 0 allocation and 0 shortage."""
    zero_df = pd.DataFrame([{"store_id": "STORE_A", "predicted_units": 0.0}])
    res = allocate_inventory_lp(zero_df, total_available_units=500)
    assert res["allocated_units"].iloc[0] == 0
    assert res["shortage"].iloc[0] == 0


def test_lp_integer_output_types(standard_forecast):
    """Verify allocated units are integer-typed."""
    res = allocate_inventory_lp(standard_forecast, total_available_units=1000)
    for val in res["allocated_units"]:
        assert isinstance(val, (int, pd.Int64Dtype, type(pd.Series([1]).dtype))) or val == int(val)


def test_lp_negative_inventory_rejection(standard_forecast):
    """Verify negative inventory raises ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        allocate_inventory_lp(standard_forecast, total_available_units=-100)


def test_lp_empty_forecast():
    """Verify empty input returns structured empty DataFrame with summary."""
    empty_df = pd.DataFrame(columns=["store_id", "predicted_units"])
    res = allocate_inventory_lp(empty_df, total_available_units=100)
    assert res.empty
    assert "store_id" in res.columns
