"""
Performance and Response Latency Test Suite (Stage 23).
"""
import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_latency():
    """Verify GET /health responds within 500 milliseconds."""
    t0 = time.perf_counter()
    res = client.get("/health")
    dt = time.perf_counter() - t0
    assert res.status_code == 200
    assert dt < 0.5, f"Health check took {dt:.3f}s (> 0.5s)"


def test_forecast_latency():
    """Verify GET /forecast (7-day horizon) completes within 2.0 seconds."""
    t0 = time.perf_counter()
    res = client.get("/forecast?horizon_days=7")
    dt = time.perf_counter() - t0
    assert res.status_code == 200
    assert dt < 2.0, f"Forecast took {dt:.3f}s (> 2.0s)"


def test_allocation_latency():
    """Verify POST /allocate completes within 1.0 second."""
    payload = {
        "total_available_units": 1000,
        "method": "proportional",
        "horizon_days": 7,
    }
    t0 = time.perf_counter()
    res = client.post("/allocate", json=payload)
    dt = time.perf_counter() - t0
    assert res.status_code == 200
    assert dt < 1.0, f"Allocation took {dt:.3f}s (> 1.0s)"


def test_repeated_requests_throughput():
    """Verify repeated calls do not degrade in performance."""
    payload = {
        "total_available_units": 1000,
        "method": "proportional",
        "horizon_days": 7,
    }
    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        res = client.post("/allocate", json=payload)
        latencies.append(time.perf_counter() - t0)
        assert res.status_code == 200

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 0.5, f"Average repeated latency was {avg_latency:.3f}s"
