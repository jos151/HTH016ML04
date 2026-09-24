from pathlib import Path
import pandas as pd

STORE_IDS = [
    "STORE_1",
    "STORE_2",
    "STORE_3",
    "STORE_4",
    "STORE_5",
]

SKU_IDS = [
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


def load_demand_data(filepath=None) -> pd.DataFrame:
    """Loads demand data from /data/sales.csv, filters to 5 store IDs and 10 SKU IDs,
    reshapes to long format [date, store_id, sku_id, units_sold], and fills missing values with 0.
    """
    if filepath is None:
        base_dir = Path(__file__).resolve().parent.parent
        filepath = base_dir / "data" / "sales.csv"
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Sales dataset not found at: {filepath}")

    df = pd.read_csv(filepath)

    # Standardize column naming if variations exist
    rename_cols = {}
    if "item_id" in df.columns and "sku_id" not in df.columns:
        rename_cols["item_id"] = "sku_id"
    if "Store" in df.columns and "store_id" not in df.columns:
        rename_cols["Store"] = "store_id"
    if rename_cols:
        df = df.rename(columns=rename_cols)

    # Filter to exactly 5 hardcoded store_ids and 10 hardcoded sku_ids
    df = df[df["store_id"].isin(STORE_IDS) & df["sku_id"].isin(SKU_IDS)]

    # Check whether data is wide (M5-style date columns) or already long format
    if "date" in df.columns and "units_sold" in df.columns:
        df_long = df[["date", "store_id", "sku_id", "units_sold"]].copy()
    else:
        metadata_cols = {"id", "dept_id", "cat_id", "state_id", "store_id", "sku_id"}
        value_vars = [c for c in df.columns if c not in metadata_cols]
        df_long = pd.melt(
            df,
            id_vars=["store_id", "sku_id"],
            value_vars=value_vars,
            var_name="date",
            value_name="units_sold",
        )
        df_long = df_long[["date", "store_id", "sku_id", "units_sold"]]

    # Fill missing values with 0
    df_long["units_sold"] = pd.to_numeric(df_long["units_sold"], errors="coerce").fillna(0)
    df_long = df_long.fillna(0)

    return df_long


if __name__ == "__main__":
    df = load_demand_data()
    print(df.head())
    print(df.shape)
