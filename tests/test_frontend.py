"""
Automated unit and integration tests for frontend API interface layer.
"""

from frontend.app import fetch_backend_health, call_allocate_api, call_simulate_api


def test_frontend_health_check():
    """Validates that fetch_backend_health returns valid health metadata."""
    ok, data, err = fetch_backend_health()
    assert ok is True, f"Health check failed: {err}"
    assert data is not None
    assert data.get("status") == "ok"
    assert data.get("data_loaded") is True
    assert data.get("store_count") == 5
    assert data.get("sku_count") == 10
    assert data.get("row_count") > 0


def test_frontend_call_allocate_baseline():
    """Validates frontend allocation call with 1000 inventory units over 7 days."""
    ok, data, err = call_allocate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=False,
        method="proportional",
        promo_boost=None,
    )
    assert ok is True, f"Allocate call failed: {err}"
    assert data is not None
    assert "summary" in data
    assert "allocations" in data

    summary = data["summary"]
    assert summary["total_available_units"] == 1000.0
    assert summary["total_allocated_units"] == 1000.0
    assert summary["total_forecasted_demand"] > 0
    assert summary["total_shortage"] == summary["total_forecasted_demand"] - 1000.0

    allocations = data["allocations"]
    assert len(allocations) == 5
    store_ids = {a["store_id"] for a in allocations}
    assert store_ids == {"STORE_1", "STORE_2", "STORE_3", "STORE_4", "STORE_5"}


def test_frontend_call_allocate_invalid_method():
    """Validates that frontend cleanly catches and surfaces API validation error for invalid method."""
    ok, data, err = call_allocate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=False,
        method="heuristic_unknown",
        promo_boost=None,
    )
    assert ok is False
    assert data is None
    assert "heuristic_unknown" in err or "422" in err or "Unknown" in err or "supported" in err


def test_frontend_call_allocate_lp():
    """Validates that frontend successfully calls POST /allocate with method='lp'."""
    ok, data, err = call_allocate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=False,
        method="lp",
        promo_boost=None,
    )
    assert ok is True, f"LP allocation failed: {err}"
    assert data is not None
    assert "allocations" in data
    assert len(data["allocations"]) == 5
    assert data["summary"]["total_allocated_units"] <= 1000.0


def test_frontend_call_simulate_promo():
    """Validates frontend promotion simulation call."""
    ok, data, err = call_simulate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=False,
        promo_boost={"STORE_1": 1.30},
    )
    assert ok is True, f"Simulate call failed: {err}"
    assert data is not None
    assert "baseline" in data
    assert "adjusted" in data
    assert "demand_lift_percentage" in data
    assert data["demand_lift_percentage"] > 0
    assert data["adjusted"]["total_demand"] > data["baseline"]["total_demand"]


def test_frontend_call_simulate_holiday():
    """Validates frontend holiday simulation call."""
    ok, data, err = call_simulate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=True,
        promo_boost=None,
    )
    assert ok is True, f"Simulate call failed: {err}"
    assert data is not None
    assert data["demand_lift_percentage"] > 0
    assert data["adjusted"]["total_demand"] > data["baseline"]["total_demand"]
