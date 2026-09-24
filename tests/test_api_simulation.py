"""
API Test Suite for Scenario Simulation Endpoints (Stage 15).
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_simulate_baseline_vs_promotion():
    """Verify POST /simulate returns baseline vs adjusted scenarios with lift percentage."""
    payload = {
        "total_available_units": 1000,
        "horizon_days": 7,
        "is_holiday_week": False,
        "promo_boost": {"STORE_1": 1.30},
    }
    res = client.post("/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "baseline" in data and "adjusted" in data
    assert data["adjusted"]["total_demand"] > data["baseline"]["total_demand"]
    assert data["demand_lift_percentage"] > 0
    assert data["shortage_change"] >= 0


def test_simulate_holiday_mode():
    """Verify POST /simulate with is_holiday_week=True."""
    payload = {
        "total_available_units": 1000,
        "horizon_days": 7,
        "is_holiday_week": True,
    }
    res = client.post("/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["adjusted"]["total_demand"] > data["baseline"]["total_demand"]
