"""
Test Suite for Data Validation and Quality Auditing (Stage 4).
"""
from pathlib import Path
import pandas as pd
import pytest
from backend.data_loader import (
    load_demand_data,
    validate_sales_df,
    get_data_quality_report,
    validate_uploaded_sales_data,
)


def test_file_not_found():
    """Verify FileNotFound error when file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_demand_data(file_path=Path("non_existent_sales_file.csv"))


def test_unsupported_file_extension(tmp_path: Path):
    """Verify rejection for unsupported file extensions like .txt or .json."""
    txt_file = tmp_path / "sales.txt"
    txt_file.write_text("date,store_id,sku_id,units_sold\n2023-01-01,STORE_1,SKU_01,10")
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_demand_data(file_path=txt_file)


def test_empty_csv_file(tmp_path: Path):
    """Verify rejection for an empty CSV file."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    with pytest.raises(ValueError):
        load_demand_data(file_path=empty_file)


def test_input_dataframe_immutability():
    """Verify validate_sales_df does not unexpectedly mutate input DataFrame in place."""
    raw_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02"],
        "store_id": ["STORE_1", "STORE_2"],
        "sku_id": ["SKU_01", "SKU_02"],
        "units_sold": [10.0, 20.0],
    })
    original_copy = raw_df.copy(deep=True)
    validated = validate_sales_df(raw_df)
    assert raw_df.equals(original_copy)
    assert not validated.empty


def test_duplicate_record_rejection(tmp_path: Path):
    """Verify duplicate date-store-SKU records are flagged."""
    dup_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01"],
        "store_id": ["STORE_1", "STORE_1"],
        "sku_id": ["SKU_01", "SKU_01"],
        "units_sold": [10.0, 15.0],
    })
    csv_file = tmp_path / "dup.csv"
    dup_df.to_csv(csv_file, index=False)
    with pytest.raises(ValueError, match="(?i)duplicate"):
        load_demand_data(file_path=csv_file)


def test_validate_uploaded_sales_data_success():
    """Verify upload validator passes a valid sales CSV."""
    csv_bytes = b"date,store_id,sku_id,units_sold\n2023-01-01,STORE_1,SKU_01,10\n2023-01-02,STORE_1,SKU_01,15\n"
    res = validate_uploaded_sales_data(csv_bytes, "new_sales.csv")
    assert res["valid"] is True
    assert res["row_count"] == 2
    assert len(res["errors"]) == 0


def test_validate_uploaded_sales_data_invalid_extension():
    """Verify upload validator rejects non-CSV/Excel files."""
    res = validate_uploaded_sales_data(b"data", "sales.pdf")
    assert res["valid"] is False
    assert any("unsupported" in e.lower() or "extension" in e.lower() for e in res["errors"])


def test_validate_uploaded_sales_data_negative_units():
    """Verify upload validator catches negative values and missing columns."""
    bad_csv = b"date,store_id,units_sold\n2023-01-01,STORE_1,-10\n"
    res = validate_uploaded_sales_data(bad_csv, "bad.csv")
    assert res["valid"] is False
    assert any("missing required" in e.lower() for e in res["errors"])


def test_data_quality_report_metrics():
    """Verify data quality report returns completeness, zero-demand count, and integrity scores."""
    report = get_data_quality_report()
    assert report["row_count"] > 0
    assert report["store_count"] == 5
    assert report["sku_count"] == 10
    assert report["status"] == "Passed"
    assert report["negative_sales_count"] == 0
    assert sum(report["missing_values"].values()) == 0
