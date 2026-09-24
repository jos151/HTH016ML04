"""
Test Suite for File Upload Validation & Schema Ingestion (Stage 16).
"""
import pytest
from backend.data_loader import validate_uploaded_sales_data


def test_upload_valid_csv():
    """Verify validation passes for properly formatted CSV bytes."""
    valid_csv = (
        b"date,store_id,sku_id,units_sold\n"
        b"2023-01-01,STORE_1,SKU_01,25.0\n"
        b"2023-01-01,STORE_2,SKU_01,30.0\n"
    )
    res = validate_uploaded_sales_data(valid_csv, "batch_sales.csv")
    assert res["valid"] is True
    assert res["row_count"] == 2
    assert len(res["errors"]) == 0
    assert res["status"] == "Passed"


def test_upload_missing_required_column():
    """Verify validation catches missing columns (e.g. sku_id missing)."""
    bad_csv = b"date,store_id,units_sold\n2023-01-01,STORE_1,25.0\n"
    res = validate_uploaded_sales_data(bad_csv, "bad.csv")
    assert res["valid"] is False
    assert any("missing required" in e.lower() for e in res["errors"])


def test_upload_invalid_dates_and_negative_units():
    """Verify upload validator catches negative values and unparseable dates."""
    corrupt_csv = (
        b"date,store_id,sku_id,units_sold\n"
        b"bad-date,STORE_1,SKU_01,-10.0\n"
    )
    res = validate_uploaded_sales_data(corrupt_csv, "corrupt.csv")
    assert res["valid"] is False
    assert len(res["errors"]) >= 2


def test_upload_unsupported_extension():
    """Verify upload validator rejects non-CSV/Excel files."""
    res = validate_uploaded_sales_data(b"binary", "report.exe")
    assert res["valid"] is False
    assert any("unsupported" in e.lower() for e in res["errors"])
