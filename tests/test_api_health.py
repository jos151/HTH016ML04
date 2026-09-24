"""
API Test Suite for Health and Metadata Endpoints (Stage 13).
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_health():
    """Verify GET /health returns 200, status=ok, and metadata dimensions without secrets."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["data_loaded"] is True
    assert data["row_count"] == 36550
    assert data["store_count"] == 5
    assert data["sku_count"] == 10
    assert data["minimum_date"] == "2022-01-01"
    assert data["maximum_date"] == "2024-01-01"
    # Ensure no secret or environment path leakage in health payload
    assert "password" not in str(data).lower()
    assert "token" not in str(data).lower()


def test_api_metadata():
    """Verify GET /metadata returns dimensions, stores, and SKUs."""
    res = client.get("/metadata")
    assert res.status_code == 200
    data = res.json()
    assert len(data["stores"]) == 5
    assert len(data["skus"]) == 10
    assert "STORE_1" in data["stores"]
    assert "SKU_01" in data["skus"]


def test_api_stores_and_skus_endpoints():
    """Verify GET /stores and GET /skus endpoints."""
    res_stores = client.get("/stores")
    assert res_stores.status_code == 200
    assert res_stores.json() == ["STORE_1", "STORE_2", "STORE_3", "STORE_4", "STORE_5"]

    res_skus = client.get("/skus")
    assert res_skus.status_code == 200
    assert len(res_skus.json()) == 10
