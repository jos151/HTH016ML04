"""
API Test Suite for Inventory Allocation Endpoints (Stage 15).
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_allocate_proportional_endpoint():
    """Verify POST /allocate with proportional method."""
    payload = {
        "total_available_units": 1000,
        "method": "proportional",
        "horizon_days": 7,
        "is_holiday_week": False,
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data and "allocations" in data
    assert data["summary"]["total_allocated_units"] <= 1000
    assert len(data["allocations"]) == 5
    assert data["summary"]["remaining_inventory"] == max(0, 1000 - data["summary"]["total_allocated_units"])


def test_allocate_lp_endpoint():
    """Verify POST /allocate with LP solver method."""
    payload = {
        "total_available_units": 1000,
        "method": "lp",
        "horizon_days": 7,
        "is_holiday_week": False,
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data and "allocations" in data
    assert data["summary"]["total_allocated_units"] <= 1000
    assert len(data["allocations"]) == 5


def test_allocate_sku_granular_endpoint():
    """Verify POST /allocate/sku multi-item endpoint."""
    payload = {
        "total_available_units": 5000,
        "horizon_days": 7,
        "method": "proportional",
        "store_priorities": {"STORE_1": 1.5},
    }
    res = client.post("/allocate/sku", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["allocations"]) > 0
    first = data["allocations"][0]
    assert "warehouse_id" in first
    assert "sku_id" in first
    assert "store_id" in first
    assert "allocated_units" in first


def test_allocate_negative_inventory_rejection():
    """Verify POST /allocate rejects negative inventory with 422 Unprocessable Entity."""
    payload = {
        "total_available_units": -500,
        "method": "proportional",
        "horizon_days": 7,
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code == 422


def test_allocate_invalid_method_rejection():
    """Verify POST /allocate rejects unknown allocation method."""
    payload = {
        "total_available_units": 1000,
        "method": "heuristic_bogus",
        "horizon_days": 7,
    }
    res = client.post("/allocate", json=payload)
    assert res.status_code in (400, 422)
