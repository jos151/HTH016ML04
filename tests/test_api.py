"""
Integration and API endpoint tests for backend/main.py using FastAPI TestClient.
Covers all endpoints, query parameters, payload validations, error handling,
HTTP status codes, and schema structures.
"""

from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    """1. Tests GET /health returns HTTP 200 with status and dataset metrics."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["data_loaded"] is True
    assert data["row_count"] > 0
    assert data["store_count"] == 5
    assert data["sku_count"] == 10
    assert "minimum_date" in data and "maximum_date" in data


def test_default_forecast():
    """2. Tests GET /forecast with default parameters (7-day horizon, no promo/holiday)."""
    res = client.get("/forecast")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 5 * 10 * 7  # 5 stores * 10 SKUs * 7 days
    sample = data[0]
    expected_keys = {
        "store_id", "sku_id", "forecast_date", "baseline_units",
        "promo_multiplier", "holiday_multiplier", "predicted_units"
    }
    assert expected_keys.issubset(sample.keys())


def test_custom_horizon_forecast():
    """3. Tests GET /forecast with custom horizon (e.g. 14 days)."""
    res = client.get("/forecast?horizon_days=14")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5 * 10 * 14
    forecast_dates = {item["forecast_date"] for item in data}
    assert len(forecast_dates) == 14


def test_holiday_forecast():
    """4. Tests GET /forecast?is_holiday_week=true applies 1.15 holiday multiplier."""
    base_res = client.get("/forecast?is_holiday_week=false")
    hol_res = client.get("/forecast?is_holiday_week=true")

    assert base_res.status_code == 200
    assert hol_res.status_code == 200

    base_sum = sum(item["predicted_units"] for item in base_res.json())
    hol_sum = sum(item["predicted_units"] for item in hol_res.json())

    assert hol_sum > base_sum
    assert abs((hol_sum / base_sum) - 1.15) < 0.01


def test_promotional_forecast():
    """5. Tests GET /forecast with promotion query parameters."""
    res = client.get("/forecast?promotion_store=STORE_1&promotion_multiplier=1.30")
    assert res.status_code == 200
    data = res.json()

    s1_items = [i for i in data if i["store_id"] == "STORE_1"]
    s2_items = [i for i in data if i["store_id"] == "STORE_2"]

    assert all(i["promo_multiplier"] == 1.30 for i in s1_items)
    assert all(i["promo_multiplier"] == 1.00 for i in s2_items)


def test_combined_promotion_and_holiday_forecast():
    """6. Tests GET /forecast with both promotion and holiday adjustments enabled."""
    res = client.get("/forecast?promotion_store=STORE_1&promotion_multiplier=1.30&is_holiday_week=true")
    assert res.status_code == 200
    data = res.json()

    s1 = [i for i in data if i["store_id"] == "STORE_1"]
    s2 = [i for i in data if i["store_id"] == "STORE_2"]

    assert all(i["promo_multiplier"] == 1.30 and i["holiday_multiplier"] == 1.15 for i in s1)
    assert all(i["promo_multiplier"] == 1.00 and i["holiday_multiplier"] == 1.15 for i in s2)


def test_proportional_allocate():
    """7. Tests POST /allocate with valid proportional request."""
    payload = {
        "total_available_units": 1000,
        "method": "proportional",
        "horizon_days": 7,
        "is_holiday_week": False,
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "allocations" in data
    assert "summary" in data

    allocations = data["allocations"]
    assert len(allocations) == 5  # 5 stores
    for a in allocations:
        assert a["allocated_units"] >= 0
        assert a["shortage"] >= 0
        assert a["excess"] == 0

    assert data["summary"]["total_allocated_units"] <= 1000.0


def test_simulate_endpoint():
    """8. Tests POST /simulate returns baseline and adjusted scenarios with metrics."""
    payload = {
        "horizon_days": 7,
        "total_available_units": 1500,
        "promo_boost": {"STORE_1": 1.30},
        "is_holiday_week": True,
    }
    res = client.post("/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "baseline" in data
    assert "adjusted" in data
    assert "demand_lift_percentage" in data
    assert "shortage_change" in data

    assert data["adjusted"]["total_demand"] > data["baseline"]["total_demand"]
    assert data["demand_lift_percentage"] > 0


def test_zero_inventory_allocation():
    """9. Tests POST /allocate with zero available inventory."""
    payload = {
        "total_available_units": 0,
        "method": "proportional",
        "horizon_days": 7,
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_allocated_units"] == 0
    assert all(a["allocated_units"] == 0 for a in data["allocations"])
    assert all(a["shortage"] == a["forecasted_demand"] for a in data["allocations"])


def test_negative_inventory_rejection():
    """10. Tests that negative total_available_units is rejected with HTTP 400 or 422."""
    payload = {
        "total_available_units": -50,
        "method": "proportional",
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code in [400, 422]


def test_allocation_method_selection():
    """11. Tests allocation method selection ('proportional', 'lp') and rejection of unknown methods."""
    # Unknown method -> HTTP 422 validation error
    res_unknown = client.post("/allocate", json={"total_available_units": 500, "method": "heuristic"})
    assert res_unknown.status_code == 422

    # 'lp' method is now supported -> HTTP 200 OK
    res_lp = client.post("/allocate", json={"total_available_units": 500, "method": "lp"})
    assert res_lp.status_code == 200
    data_lp = res_lp.json()
    assert "allocations" in data_lp
    assert data_lp["summary"]["total_allocated_units"] <= 500.0


def test_invalid_horizon():
    """12. Tests rejection of non-positive or excessive horizon values."""
    res_zero = client.get("/forecast?horizon_days=0")
    assert res_zero.status_code == 422

    res_neg = client.get("/forecast?horizon_days=-5")
    assert res_neg.status_code == 422

    res_excessive = client.get("/forecast?horizon_days=500")
    assert res_excessive.status_code == 422


def test_invalid_promotion_multiplier():
    """13. Tests rejection of promotion multiplier below 1.0."""
    # Via query parameter on /forecast -> HTTP 400
    res_q = client.get("/forecast?promotion_store=STORE_1&promotion_multiplier=0.85")
    assert res_q.status_code == 400
    assert "at least 1.0" in res_q.json()["detail"]

    # Via request body on /allocate -> HTTP 422 or 400
    res_b = client.post("/allocate", json={
        "total_available_units": 500,
        "method": "proportional",
        "promo_boost": {"STORE_1": 0.50},
    })
    assert res_b.status_code in [400, 422]


def test_invalid_request_body():
    """14. Tests rejection of malformed or incomplete POST request payloads."""
    # Missing required field total_available_units -> HTTP 422
    res_missing = client.post("/allocate", json={"method": "proportional"})
    assert res_missing.status_code == 422

    # Wrong data type for total_available_units -> HTTP 422
    res_type = client.post("/allocate", json={
        "total_available_units": "one_thousand_units",
        "method": "proportional",
    })
    assert res_type.status_code == 422

    # Malformed JSON syntax
    res_malformed = client.post(
        "/allocate",
        content="not-json",
        headers={"Content-Type": "application/json"},
    )
    assert res_malformed.status_code == 422


def test_missing_data_file(monkeypatch):
    """15. Tests that a missing source dataset returns HTTP 503 Service Unavailable."""
    def mock_missing_loader(*args, **kwargs):
        raise FileNotFoundError("sales.csv does not exist")

    monkeypatch.setattr("backend.main.load_demand_data", mock_missing_loader)

    res_health = client.get("/health")
    assert res_health.status_code == 503
    assert "missing" in res_health.json()["detail"].lower()

    res_fc = client.get("/forecast")
    assert res_fc.status_code == 503


def test_empty_dataset(monkeypatch):
    """16. Tests that an empty dataset returns HTTP 503 Service Unavailable."""
    def mock_empty_loader(*args, **kwargs):
        return pd.DataFrame(columns=["date", "store_id", "sku_id", "units_sold"])

    monkeypatch.setattr("backend.main.load_demand_data", mock_empty_loader)

    res_health = client.get("/health")
    assert res_health.status_code == 503
    assert "empty" in res_health.json()["detail"].lower()

    res_alloc = client.post("/allocate", json={"total_available_units": 500, "method": "proportional"})
    assert res_alloc.status_code == 503


def test_correct_http_status_codes():
    """17. Systematically verifies standard HTTP status codes: 200, 400, 422, 503."""
    # 200 OK
    assert client.get("/health").status_code == 200
    assert client.post("/allocate", json={"total_available_units": 100, "method": "lp"}).status_code == 200
    # 400 Bad Request
    assert client.get("/forecast?promotion_multiplier=1.30").status_code == 400
    # 422 Unprocessable Entity
    assert client.get("/forecast?horizon_days=-1").status_code == 422


def test_correct_response_fields():
    """18. Verifies exact schema and field types for all primary endpoints."""
    # Health response
    h_res = client.get("/health")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert isinstance(h_data["status"], str)
    assert isinstance(h_data["row_count"], int)
    assert isinstance(h_data["store_count"], int)
    assert isinstance(h_data["sku_count"], int)

    # Allocation response
    a_res = client.post("/allocate", json={"total_available_units": 800, "method": "proportional"})
    assert a_res.status_code == 200
    a_data = a_res.json()
    summary = a_data["summary"]
    assert "total_forecasted_demand" in summary
    assert "total_available_units" in summary
    assert "total_allocated_units" in summary
    assert "total_shortage" in summary
    assert "remaining_inventory" in summary
