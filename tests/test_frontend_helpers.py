"""
Test Suite for Frontend Helper Logic and Presentation Mapping (Stage 19).
"""
import pytest
from frontend.app import (
    API_BASE_URL,
    fetch_backend_health,
    call_allocate_api,
    call_simulate_api,
    call_forecast_bounds_api,
    call_allocate_sku_api,
    call_safety_stock_api,
    call_data_quality_api,
)


def test_frontend_api_base_url():
    """Verify default API base URL is configured."""
    assert API_BASE_URL.startswith("http")


def test_frontend_health_helper():
    """Verify fetch_backend_health returns valid health data."""
    ok, data, err = fetch_backend_health()
    assert ok is True, f"Health call failed: {err}"
    assert data is not None
    assert data["status"] == "ok"


def test_frontend_allocate_helper():
    """Verify call_allocate_api creates valid payload and retrieves response."""
    ok, data, err = call_allocate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=False,
        method="proportional",
    )
    assert ok is True, f"Allocation helper failed: {err}"
    assert data["summary"]["total_allocated_units"] <= 1000
    assert len(data["allocations"]) == 5


def test_frontend_simulate_helper():
    """Verify call_simulate_api handles scenario comparative payload."""
    ok, data, err = call_simulate_api(
        total_available_units=1000,
        horizon_days=7,
        is_holiday_week=True,
    )
    assert ok is True, f"Simulation helper failed: {err}"
    assert "baseline" in data and "adjusted" in data


def test_frontend_forecast_bounds_helper():
    """Verify call_forecast_bounds_api helper."""
    ok, data, err = call_forecast_bounds_api(horizon_days=7)
    assert ok is True, f"Bounds helper failed: {err}"
    assert isinstance(data, list)
    assert len(data) == 5 * 10 * 7


def test_frontend_safety_stock_helper():
    """Verify call_safety_stock_api helper."""
    ok, data, err = call_safety_stock_api(lead_time_days=7, target_service_level=0.95)
    assert ok is True, f"Safety stock helper failed: {err}"
    assert isinstance(data, list)
    assert len(data) == 10  # 10 SKUs


def test_frontend_data_quality_helper():
    """Verify call_data_quality_api helper."""
    ok, data, err = call_data_quality_api()
    assert ok is True, f"Data quality helper failed: {err}"
    assert data["status"] == "Passed"
