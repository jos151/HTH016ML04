"""
API Test Suite for Demand Forecasting Endpoints (Stage 14).
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_forecast_default_and_custom_horizon():
    """Verify GET /forecast with default 7 days and custom 14 days."""
    res7 = client.get("/forecast")
    assert res7.status_code == 200
    assert len(res7.json()) == 5 * 10 * 7

    res14 = client.get("/forecast?horizon_days=14")
    assert res14.status_code == 200
    assert len(res14.json()) == 5 * 10 * 14


def test_forecast_bounds_endpoint():
    """Verify GET /forecast/bounds returns parametric bounds and non-negative limits."""
    res = client.get("/forecast/bounds?horizon_days=7&confidence_level=0.90")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5 * 10 * 7
    first = data[0]
    assert "lower_confidence_bound" in first
    assert "upper_confidence_bound" in first
    assert "uncertainty_risk" in first
    assert first["lower_confidence_bound"] <= first["predicted_units"]
    assert first["upper_confidence_bound"] >= first["predicted_units"]
    assert first["lower_confidence_bound"] >= 0.0


def test_forecast_invalid_horizon_rejection():
    """Verify non-positive or excessive horizons return HTTP 422 or 400."""
    res_zero = client.get("/forecast?horizon_days=0")
    assert res_zero.status_code in (400, 422)

    res_neg = client.get("/forecast?horizon_days=-5")
    assert res_neg.status_code in (400, 422)

    res_large = client.get("/forecast?horizon_days=500")
    assert res_large.status_code in (400, 422)


def test_forecast_invalid_promo_multiplier_rejection():
    """Verify promo multiplier below 1.0 returns 400."""
    res = client.get("/forecast?promotion_store=STORE_1&promotion_multiplier=0.85")
    assert res.status_code == 400
    assert "at least 1.0" in res.json()["detail"]

    res2 = client.get("/forecast?promotion_store=STORE_1&promotion_multiplier=-0.5")
    assert res2.status_code == 400
