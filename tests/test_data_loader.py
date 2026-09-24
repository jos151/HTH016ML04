"""
Unit tests for backend/data_loader.py covering validation, grid completion,
filtering, error handling, and numeric conversions.
"""

from pathlib import Path
import pandas as pd
import pytest
from backend.data_loader import load_demand_data, STORE_IDS, SKU_IDS


def test_valid_loading_default():
    """1. Tests valid default loading from data/processed/sales.csv."""
    df = load_demand_data()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert set(["date", "store_id", "sku_id", "units_sold"]).issubset(df.columns)
    assert df["store_id"].nunique() == 5
    assert df["sku_id"].nunique() == 10
    assert (df["units_sold"] >= 0).all()


def test_missing_required_column(tmp_path: Path):
    """2. Tests rejection when a required column (e.g., units_sold) is missing."""
    bad_df = pd.DataFrame({
        "date": ["2023-01-01"],
        "store_id": ["STORE_1"],
        "sku_id": ["SKU_01"],
    })
    csv_file = tmp_path / "missing_col.csv"
    bad_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="Missing required column"):
        load_demand_data(file_path=csv_file)


def test_invalid_date(tmp_path: Path):
    """3. Tests rejection of unparseable date values."""
    bad_df = pd.DataFrame({
        "date": ["not-a-valid-date"],
        "store_id": ["STORE_1"],
        "sku_id": ["SKU_01"],
        "units_sold": [10],
    })
    csv_file = tmp_path / "invalid_date.csv"
    bad_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="unparseable or invalid date values"):
        load_demand_data(file_path=csv_file)


def test_date_parsing(tmp_path: Path):
    """3b. Tests that dates in valid formats are safely parsed to ISO YYYY-MM-DD."""
    dates_df = pd.DataFrame({
        "date": ["2023/01/01", "2023-01-02", "2023/01/03"],
        "store_id": ["STORE_1", "STORE_1", "STORE_1"],
        "sku_id": ["SKU_01", "SKU_01", "SKU_01"],
        "units_sold": [10, 20, 30],
    })
    csv_file = tmp_path / "date_parsing.csv"
    dates_df.to_csv(csv_file, index=False)

    df = load_demand_data(file_path=csv_file)
    parsed_dates = df["date"].tolist()
    assert parsed_dates == ["2023-01-01", "2023-01-02", "2023-01-03"]


def test_negative_units_sold(tmp_path: Path):
    """4. Tests rejection of negative units_sold values."""
    bad_df = pd.DataFrame({
        "date": ["2023-01-01"],
        "store_id": ["STORE_1"],
        "sku_id": ["SKU_01"],
        "units_sold": [-5],
    })
    csv_file = tmp_path / "negative_units.csv"
    bad_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="negative units_sold"):
        load_demand_data(file_path=csv_file)


def test_missing_store_id(tmp_path: Path):
    """5. Tests rejection when store_id is empty or null."""
    bad_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02"],
        "store_id": ["STORE_1", ""],
        "sku_id": ["SKU_01", "SKU_01"],
        "units_sold": [10, 15],
    })
    csv_file = tmp_path / "missing_store.csv"
    bad_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="missing or empty store_id"):
        load_demand_data(file_path=csv_file)


def test_missing_sku_id(tmp_path: Path):
    """6. Tests rejection when sku_id is empty or null."""
    bad_df = pd.DataFrame({
        "date": ["2023-01-01"],
        "store_id": ["STORE_1"],
        "sku_id": [None],
        "units_sold": [10],
    })
    csv_file = tmp_path / "missing_sku.csv"
    bad_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="missing or empty sku_id"):
        load_demand_data(file_path=csv_file)


def test_duplicate_record(tmp_path: Path):
    """7. Tests detection and rejection of duplicate date-store-SKU combinations."""
    dup_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01"],
        "store_id": ["STORE_1", "STORE_1"],
        "sku_id": ["SKU_01", "SKU_01"],
        "units_sold": [10, 12],
    })
    csv_file = tmp_path / "duplicates.csv"
    dup_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="duplicate record"):
        load_demand_data(file_path=csv_file)


def test_store_filtering(tmp_path: Path):
    """8. Tests filtering by specific store_ids."""
    sample_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01"],
        "store_id": ["STORE_1", "STORE_2"],
        "sku_id": ["SKU_01", "SKU_01"],
        "units_sold": [10, 20],
    })
    csv_file = tmp_path / "sample_stores.csv"
    sample_df.to_csv(csv_file, index=False)

    df = load_demand_data(file_path=csv_file, store_ids=["STORE_1"])
    assert df["store_id"].unique().tolist() == ["STORE_1"]
    assert len(df) == 1


def test_sku_filtering(tmp_path: Path):
    """9. Tests filtering by specific sku_ids."""
    sample_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01"],
        "store_id": ["STORE_1", "STORE_1"],
        "sku_id": ["SKU_01", "SKU_02"],
        "units_sold": [10, 20],
    })
    csv_file = tmp_path / "sample_skus.csv"
    sample_df.to_csv(csv_file, index=False)

    df = load_demand_data(file_path=csv_file, sku_ids=["SKU_02"])
    assert df["sku_id"].unique().tolist() == ["SKU_02"]
    assert len(df) == 1


def test_missing_date_completion(tmp_path: Path):
    """10. Tests that incomplete combinations are grid-completed with zero units_sold."""
    # STORE_1 has both dates, but STORE_2 is missing 2023-01-02
    sparse_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02", "2023-01-01"],
        "store_id": ["STORE_1", "STORE_1", "STORE_2"],
        "sku_id": ["SKU_01", "SKU_01", "SKU_01"],
        "units_sold": [15, 20, 25],
    })
    csv_file = tmp_path / "sparse.csv"
    sparse_df.to_csv(csv_file, index=False)

    df = load_demand_data(file_path=csv_file)
    # Expected grid: 2 dates x 2 stores x 1 SKU = 4 rows
    assert len(df) == 4
    store2_d2 = df[(df["store_id"] == "STORE_2") & (df["date"] == "2023-01-02")]
    assert len(store2_d2) == 1
    assert store2_d2["units_sold"].iloc[0] == 0.0


def test_correct_sorting(tmp_path: Path):
    """11. Tests that output is sorted by store_id, sku_id, date."""
    unsorted_df = pd.DataFrame({
        "date": ["2023-01-02", "2023-01-01", "2023-01-01"],
        "store_id": ["STORE_2", "STORE_1", "STORE_2"],
        "sku_id": ["SKU_01", "SKU_01", "SKU_01"],
        "units_sold": [10, 20, 30],
    })
    csv_file = tmp_path / "unsorted.csv"
    unsorted_df.to_csv(csv_file, index=False)

    df = load_demand_data(file_path=csv_file)
    stores = df["store_id"].tolist()
    skus = df["sku_id"].tolist()
    dates = df["date"].tolist()

    assert (stores, skus, dates) == (sorted(stores), sorted(skus), dates)
    # Check strict grouping
    assert stores[0] == "STORE_1" and stores[1] == "STORE_1"
    assert stores[2] == "STORE_2" and stores[3] == "STORE_2"


def test_numeric_conversion(tmp_path: Path):
    """12. Tests that string units_sold is safely converted to numeric."""
    str_df = pd.DataFrame({
        "date": ["2023-01-01"],
        "store_id": ["STORE_1"],
        "sku_id": ["SKU_01"],
        "units_sold": ["42"],
    })
    csv_file = tmp_path / "string_units.csv"
    str_df.to_csv(csv_file, index=False)

    df = load_demand_data(file_path=csv_file)
    assert pd.api.types.is_numeric_dtype(df["units_sold"])
    assert df["units_sold"].iloc[0] == 42.0
