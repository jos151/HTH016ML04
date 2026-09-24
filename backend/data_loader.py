"""
Demand data loader module with schema validation, date grid completion, and filtering.
"""

from pathlib import Path
from typing import List, Optional, Union
import numpy as np
import pandas as pd

STORE_IDS: List[str] = [
    "STORE_1",
    "STORE_2",
    "STORE_3",
    "STORE_4",
    "STORE_5",
]

SKU_IDS: List[str] = [
    "SKU_01",
    "SKU_02",
    "SKU_03",
    "SKU_04",
    "SKU_05",
    "SKU_06",
    "SKU_07",
    "SKU_08",
    "SKU_09",
    "SKU_10",
]

REQUIRED_BASE_COLUMNS: List[str] = [
    "date",
    "store_id",
    "sku_id",
    "units_sold",
]


def _validate_columns(df: pd.DataFrame) -> None:
    """Verifies that all mandatory base columns are present."""
    missing = [c for c in REQUIRED_BASE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")


def _validate_non_empty_identifiers(df: pd.DataFrame) -> None:
    """Validates that store_id and sku_id contain no null or blank entries."""
    if df["store_id"].isnull().any() or (df["store_id"].astype(str).str.strip() == "").any():
        raise ValueError("Dataset contains missing or empty store_id values.")
    if df["sku_id"].isnull().any() or (df["sku_id"].astype(str).str.strip() == "").any():
        raise ValueError("Dataset contains missing or empty sku_id values.")


def _validate_and_parse_dates(df: pd.DataFrame) -> pd.Series:
    """Safely parses dates into ISO string (YYYY-MM-DD) or raises ValueError."""
    parsed = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    if parsed.isnull().any():
        invalid_examples = df.loc[parsed.isnull(), "date"].dropna().head(3).tolist()
        raise ValueError(
            f"Dataset contains unparseable or invalid date values: {invalid_examples}"
        )
    return parsed.dt.strftime("%Y-%m-%d")


def _validate_units_sold(df: pd.DataFrame) -> pd.Series:
    """Converts units_sold to numeric and asserts non-negative values."""
    numeric_units = pd.to_numeric(df["units_sold"], errors="coerce")
    if numeric_units.isnull().any():
        raise ValueError("Dataset contains non-numeric values in units_sold.")
    if (numeric_units < 0).any():
        neg_count = (numeric_units < 0).sum()
        raise ValueError(f"Dataset contains {neg_count} negative units_sold record(s).")
    return numeric_units


def _check_duplicates(df: pd.DataFrame) -> None:
    """Detects duplicate date-store-SKU combinations."""
    dups = df.duplicated(subset=["date", "store_id", "sku_id"], keep=False)
    if dups.any():
        dup_count = dups.sum()
        sample = df.loc[dups, ["date", "store_id", "sku_id"]].head(2).to_dict(orient="records")
        raise ValueError(
            f"Detected {dup_count} duplicate record(s) for [date, store_id, sku_id]. Example: {sample}"
        )


def load_demand_data(
    file_path: Optional[Union[str, Path]] = None,
    store_ids: Optional[List[str]] = None,
    sku_ids: Optional[List[str]] = None,
    filepath: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Loads, validates, filters, and constructs a complete date-store-SKU demand grid.

    Parameters:
        file_path: Path to sales dataset. Defaults to data/processed/sales.csv if present,
                   falling back to data/sales.csv.
        store_ids: Optional list of store IDs to filter to.
        sku_ids: Optional list of SKU IDs to filter to.
        filepath: Backwards-compatible alias for file_path.

    Returns:
        pd.DataFrame: Validated demand DataFrame sorted by store_id, sku_id, date.
    """
    path_to_use = file_path or filepath

    if path_to_use is None:
        base_dir = Path(__file__).resolve().parent.parent
        processed_path = base_dir / "data" / "processed" / "sales.csv"
        fallback_path = base_dir / "data" / "sales.csv"
        target_path = processed_path if processed_path.exists() else fallback_path
    else:
        target_path = Path(path_to_use)

    if not target_path.exists():
        raise FileNotFoundError(f"Sales dataset not found at: {target_path}")

    df = pd.read_csv(target_path)

    # Standardize column naming variations if applicable
    rename_cols = {}
    if "item_id" in df.columns and "sku_id" not in df.columns:
        rename_cols["item_id"] = "sku_id"
    if "Store" in df.columns and "store_id" not in df.columns:
        rename_cols["Store"] = "store_id"
    if rename_cols:
        df = df.rename(columns=rename_cols)

    # Check whether data is in standard long format or legacy wide format
    is_standard_long = "date" in df.columns
    if is_standard_long and "units_sold" not in df.columns:
        # It has a 'date' column, so it is a long format dataset missing required columns (e.g. units_sold)
        _validate_columns(df)

    if not ("date" in df.columns and "units_sold" in df.columns):
        # Handle wide format where dates are column headers
        metadata_cols = {"id", "dept_id", "cat_id", "state_id", "store_id", "sku_id"}
        value_vars = [c for c in df.columns if c not in metadata_cols]
        if not value_vars:
            _validate_columns(df)
        df = pd.melt(
            df,
            id_vars=[c for c in ["store_id", "sku_id"] if c in df.columns],
            value_vars=value_vars,
            var_name="date",
            value_name="units_sold",
        )

    # 1. Base validation
    _validate_columns(df)
    _validate_non_empty_identifiers(df)
    df["date"] = _validate_and_parse_dates(df)
    df["units_sold"] = _validate_units_sold(df)

    # 2. Check for duplicate records in raw input
    _check_duplicates(df)

    # 3. Filtering
    if store_ids is not None:
        df = df[df["store_id"].isin(store_ids)]
    if sku_ids is not None:
        df = df[df["sku_id"].isin(sku_ids)]

    if df.empty:
        return pd.DataFrame(
            columns=["date", "store_id", "sku_id", "units_sold", "is_promo", "promo_multiplier", "is_holiday"]
        )

    # 4. Construct complete date-store-SKU grid
    selected_stores = sorted(df["store_id"].unique().tolist())
    selected_skus = sorted(df["sku_id"].unique().tolist())
    selected_dates = sorted(df["date"].unique().tolist())

    grid_index = pd.MultiIndex.from_product(
        [selected_dates, selected_stores, selected_skus],
        names=["date", "store_id", "sku_id"],
    )
    df_grid = pd.DataFrame(index=grid_index).reset_index()

    # 5. Merge observation onto complete grid
    merged = pd.merge(
        df_grid,
        df,
        on=["date", "store_id", "sku_id"],
        how="left",
    )

    # Fill missing units_sold combinations with 0
    merged["units_sold"] = merged["units_sold"].fillna(0.0)

    # Fill optional promotional and holiday indicators
    if "is_promo" in merged.columns:
        merged["is_promo"] = merged["is_promo"].fillna(0).astype(int)
    else:
        merged["is_promo"] = 0

    if "promo_multiplier" in merged.columns:
        merged["promo_multiplier"] = merged["promo_multiplier"].fillna(1.0).astype(float)
    else:
        merged["promo_multiplier"] = 1.0

    if "is_holiday" in merged.columns:
        merged["is_holiday"] = merged["is_holiday"].fillna(0).astype(int)
    else:
        merged["is_holiday"] = 0

    # 6. Sort deterministically by store_id, sku_id, date
    result = merged.sort_values(["store_id", "sku_id", "date"]).reset_index(drop=True)
    return result


def get_data_quality_report(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Generates a comprehensive diagnostic data quality audit of the sales dataset."""
    target_df = df if df is not None else load_demand_data()

    if target_df.empty:
        return {
            "status": "Failed",
            "dataset_source": "data/processed/sales.csv",
            "is_real_data": False,
            "row_count": 0,
            "date_range": {"min": None, "max": None, "days": 0},
            "store_count": 0,
            "sku_count": 0,
            "missing_values": {},
            "duplicate_count": 0,
            "negative_sales_count": 0,
            "zero_sales_count": 0,
            "zero_sales_percentage": 0.0,
            "missing_combination_count": 0,
            "warnings": ["Dataset is empty."],
        }

    row_count = int(len(target_df))
    min_date = str(target_df["date"].min())
    max_date = str(target_df["date"].max())
    unique_dates = int(target_df["date"].nunique())
    store_count = int(target_df["store_id"].nunique())
    sku_count = int(target_df["sku_id"].nunique())

    missing_vals = {col: int(target_df[col].isnull().sum()) for col in target_df.columns}
    dup_count = int(target_df.duplicated(subset=["date", "store_id", "sku_id"]).sum())

    numeric_units = pd.to_numeric(target_df["units_sold"], errors="coerce")
    neg_count = int((numeric_units < 0).sum())
    zero_count = int((numeric_units == 0).sum())
    zero_pct = round((zero_count / max(1, row_count)) * 100.0, 2)

    # Check completeness against Cartesian product
    expected_rows = unique_dates * store_count * sku_count
    missing_combos = max(0, expected_rows - row_count)

    warnings = []
    if missing_combos > 0:
        warnings.append(f"Grid incomplete: {missing_combos} date-store-SKU combinations unobserved.")
    if zero_pct > 40.0:
        warnings.append(f"High zero-sales frequency ({zero_pct}% of records have 0 units).")

    if neg_count > 0 or dup_count > 0 or any(missing_vals.values()):
        status = "Failed"
    elif warnings:
        status = "Passed with warnings"
    else:
        status = "Passed"

    return {
        "status": status,
        "dataset_source": "data/processed/sales.csv (Retail Store POS Transactions)",
        "is_real_data": True,
        "row_count": row_count,
        "date_range": {
            "min": min_date,
            "max": max_date,
            "days": unique_dates,
        },
        "store_count": store_count,
        "sku_count": sku_count,
        "missing_values": missing_vals,
        "duplicate_count": dup_count,
        "negative_sales_count": neg_count,
        "zero_sales_count": zero_count,
        "zero_sales_percentage": zero_pct,
        "missing_combination_count": missing_combos,
        "warnings": warnings,
        "stores": sorted(target_df["store_id"].unique().tolist()),
        "skus": sorted(target_df["sku_id"].unique().tolist()),
    }


def validate_uploaded_sales_data(
    file_bytes: bytes,
    filename: str,
) -> Dict[str, Any]:
    """Validates an uploaded file (CSV or Excel) against the required demand schema."""
    import io

    clean_name = Path(filename).name.lower()
    errors = []

    if not (clean_name.endswith(".csv") or clean_name.endswith(".xlsx") or clean_name.endswith(".xls")):
        return {
            "valid": False,
            "filename": filename,
            "row_count": 0,
            "errors": [f"Unsupported file format '{Path(filename).suffix}'. Supported: .csv, .xlsx, .xls"],
            "preview": [],
            "status": "Failed",
        }

    try:
        if clean_name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as exc:
        return {
            "valid": False,
            "filename": filename,
            "row_count": 0,
            "errors": [f"File could not be parsed: {str(exc)}"],
            "preview": [],
            "status": "Failed",
        }

    # 1. Base columns
    missing_cols = [c for c in REQUIRED_BASE_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")

    if not missing_cols:
        # 2. Check identifiers
        if df["store_id"].isnull().any() or (df["store_id"].astype(str).str.strip() == "").any():
            errors.append("Dataset contains missing or empty store_id entries.")
        if df["sku_id"].isnull().any() or (df["sku_id"].astype(str).str.strip() == "").any():
            errors.append("Dataset contains missing or empty sku_id entries.")

        # 3. Check dates
        parsed_dates = pd.to_datetime(df["date"], errors="coerce", format="mixed")
        if parsed_dates.isnull().any():
            errors.append(f"Dataset contains {parsed_dates.isnull().sum()} invalid date values.")

        # 4. Check numeric units
        numeric_units = pd.to_numeric(df["units_sold"], errors="coerce")
        if numeric_units.isnull().any():
            errors.append("Dataset contains non-numeric values in units_sold.")
        if (numeric_units < 0).any():
            errors.append(f"Dataset contains {(numeric_units < 0).sum()} negative units_sold rows.")

        # 5. Check duplicates
        dups = df.duplicated(subset=["date", "store_id", "sku_id"]).sum()
        if dups > 0:
            errors.append(f"Detected {dups} duplicate records for [date, store_id, sku_id].")

    is_valid = len(errors) == 0
    preview_records = df.head(5).to_dict(orient="records") if not df.empty else []

    return {
        "valid": is_valid,
        "filename": filename,
        "row_count": int(len(df)),
        "errors": errors,
        "preview": preview_records,
        "status": "Passed" if is_valid else "Failed",
    }


if __name__ == "__main__":
    print("=" * 70)
    print("DEMAND DATA LOADER - MAIN EXECUTION CHECK")
    print("=" * 70)
    df_loaded = load_demand_data()
    print("\n--- First 5 Rows ---")
    print(df_loaded.head().to_string(index=False))

    print("\n--- Shape ---")
    print(f"Rows: {df_loaded.shape[0]:,}, Columns: {df_loaded.shape[1]}")

    print("\n--- Date Range ---")
    print(f"Min Date: {df_loaded['date'].min()} | Max Date: {df_loaded['date'].max()} | Unique: {df_loaded['date'].nunique()}")

    print("\n--- Unique Stores ---")
    print(f"Count: {df_loaded['store_id'].nunique()} -> {df_loaded['store_id'].unique().tolist()}")

    print("\n--- Unique SKUs ---")
    print(f"Count: {df_loaded['sku_id'].nunique()} -> {df_loaded['sku_id'].unique().tolist()}")

    print("\n--- Missing Values Per Column ---")
    for c, cnt in df_loaded.isnull().sum().items():
        print(f"  {c:<18}: {cnt}")

    print("\n--- Duplicate [date, store_id, sku_id] Count ---")
    dup_count = df_loaded.duplicated(subset=["date", "store_id", "sku_id"]).sum()
    print(f"Duplicates: {dup_count}")
    print("=" * 70)
