"""
Security and Defensive Validation Test Suite (Stage 22).
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.data_loader import validate_uploaded_sales_data

client = TestClient(app)


def test_security_negative_inventory_rejected():
    """Verify negative inventory in allocation payload is strictly rejected with 422."""
    res = client.post("/allocate", json={"total_available_units": -100, "method": "proportional"})
    assert res.status_code == 422


def test_security_path_traversal_in_upload():
    """Verify path traversal filenames in file uploads are sanitized and neutralized."""
    traversal_name = "../../../etc/passwd"
    res = validate_uploaded_sales_data(b"data", traversal_name)
    assert res["valid"] is False
    # Path().name strips directory components
    assert "passwd" in res["errors"][0] or "unsupported" in res["errors"][0].lower()


def test_security_spreadsheet_formula_injection_safety():
    """Verify formulas like =cmd|' /C calc'!A0 in units_sold are not evaluated and rejected as non-numeric."""
    malicious_csv = (
        b"date,store_id,sku_id,units_sold\n"
        b"2023-01-01,STORE_1,SKU_01,=cmd|' /C calc'!A0\n"
    )
    res = validate_uploaded_sales_data(malicious_csv, "exploit.csv")
    assert res["valid"] is False
    assert any("non-numeric" in e.lower() for e in res["errors"])


def test_security_malformed_json_payload():
    """Verify malformed JSON payload returns 422 Unprocessable Entity instead of 500 crash."""
    res = client.post(
        "/allocate",
        content="not-a-valid-json",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422


def test_security_no_internal_stacktrace_on_invalid_route():
    """Verify 404 or 405 error responses do not leak internal system tracebacks."""
    res = client.get("/non_existent_system_admin_route")
    assert res.status_code == 404
    assert "Traceback" not in res.text
