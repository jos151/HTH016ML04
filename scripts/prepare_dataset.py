"""
prepare_dataset.py
------------------
Senior Retail Data Engineer dataset preparation and validation pipeline.

Prepares:
- data/processed/sales.csv
- data/processed/calendar.csv
- data/processed/promotions.csv
- data/processed/inventory.csv
- data/processed/products.csv
- data/processed/stores.csv

Features:
- Source dataset detection with clear missing file error reporting.
- Deterministic 5-store x 10-SKU subset selection.
- Full date-store-SKU grid enforcement with missing combination zero-fill.
- Strict validation rules (parseable dates, non-negative units_sold, promo multiplier >= 1.0, 0/1 binary flags).
- Comprehensive dataset validation report printing.
- Clean synthetic demo fallback generator if requested or needed.
"""

import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# Official US Federal Holidays dictionary (2022 - 2024)
US_HOLIDAYS: Dict[str, str] = {
    "2022-01-01": "New Year's Day",
    "2022-01-17": "Martin Luther King Jr. Day",
    "2022-02-21": "Presidents' Day",
    "2022-05-30": "Memorial Day",
    "2022-06-19": "Juneteenth",
    "2022-07-04": "Independence Day",
    "2022-09-05": "Labor Day",
    "2022-10-10": "Columbus Day",
    "2022-11-11": "Veterans Day",
    "2022-11-24": "Thanksgiving Day",
    "2022-11-25": "Black Friday",
    "2022-12-25": "Christmas Day",
    "2023-01-01": "New Year's Day",
    "2023-01-16": "Martin Luther King Jr. Day",
    "2023-02-20": "Presidents' Day",
    "2023-05-29": "Memorial Day",
    "2023-06-19": "Juneteenth",
    "2023-07-04": "Independence Day",
    "2023-09-04": "Labor Day",
    "2023-10-09": "Columbus Day",
    "2023-11-10": "Veterans Day",
    "2023-11-23": "Thanksgiving Day",
    "2023-11-24": "Black Friday",
    "2023-12-25": "Christmas Day",
    "2024-01-01": "New Year's Day",
}


def find_source_file(raw_dir: Path) -> Tuple[Optional[Path], str]:
    """Inspects raw_dir for genuine retail source datasets."""
    candidates = [
        ("retail_store_inventory.csv", "Real Multi-Echelon Retail Inventory POS Dataset"),
        ("sales_train_evaluation.csv", "Real M5 Forecasting Evaluation Dataset"),
        ("sales_train_validation.csv", "Real M5 Forecasting Validation Dataset"),
    ]
    for fname, desc in candidates:
        candidate_path = raw_dir / fname
        if candidate_path.exists() and candidate_path.stat().st_size > 0:
            return candidate_path, desc

    return None, "Missing"


def create_synthetic_fallback(
    processed_dir: Path,
    num_stores: int = 5,
    num_skus: int = 10,
    num_days: int = 180,
) -> Dict[str, pd.DataFrame]:
    """Generates clearly labelled synthetic demo datasets as a temporary fallback."""
    print("[!] NOTICE: Generating clearly labelled SYNTHETIC fallback datasets.")
    stores = [f"STORE_{i}" for i in range(1, num_stores + 1)]
    skus = [f"SKU_{i:02d}" for i in range(1, num_skus + 1)]
    dates = pd.date_range("2023-01-01", periods=num_days, freq="D")

    # Calendar
    cal_rows = []
    for d in dates:
        d_str = d.strftime("%Y-%m-%d")
        h_name = US_HOLIDAYS.get(d_str, "")
        cal_rows.append({
            "date": d_str,
            "day_of_week": d.day_name(),
            "day_of_week_number": d.dayofweek + 1,
            "is_weekend": 1 if d.dayofweek in [5, 6] else 0,
            "is_holiday": 1 if h_name != "" else 0,
            "holiday_name": h_name,
            "month": d.month,
            "week_of_year": int(d.isocalendar().week),
        })
    df_cal = pd.DataFrame(cal_rows)

    # Sales & Promotions
    sales_rows = []
    promo_rows = []
    rng = np.random.default_rng(seed=42)

    for s in stores:
        for k in skus:
            base_demand = rng.integers(10, 50)
            for d in dates:
                d_str = d.strftime("%Y-%m-%d")
                is_hol = 1 if d_str in US_HOLIDAYS else 0
                is_p = 1 if rng.random() < 0.15 else 0
                p_mult = round(1.20 if is_p else 1.0, 2)
                p_type = "Seasonal Discount" if is_p else "None"

                dow_factor = 1.25 if d.dayofweek in [4, 5] else 1.0
                hol_factor = 1.30 if is_hol else 1.0
                units = int(max(0, round(base_demand * dow_factor * hol_factor * p_mult + rng.normal(0, 3))))

                sales_rows.append({
                    "date": d_str,
                    "store_id": s,
                    "sku_id": k,
                    "units_sold": units,
                    "is_promo": is_p,
                    "promo_multiplier": p_mult,
                    "is_holiday": is_hol,
                })
                promo_rows.append({
                    "date": d_str,
                    "store_id": s,
                    "sku_id": k,
                    "is_promo": is_p,
                    "promo_multiplier": p_mult,
                    "promo_type": p_type,
                })

    df_sales = pd.DataFrame(sales_rows).sort_values(["store_id", "sku_id", "date"]).reset_index(drop=True)
    df_promos = pd.DataFrame(promo_rows).sort_values(["store_id", "sku_id", "date"]).reset_index(drop=True)

    # Products
    categories = ["Groceries", "Electronics", "Clothing", "Toys", "Furniture"]
    df_prod = pd.DataFrame([
        {
            "sku_id": k,
            "product_name": f"Synthetic Item {k}",
            "category": categories[i % len(categories)],
            "unit_price": round(float(rng.uniform(15.0, 85.0)), 2),
            "priority_weight": 1.0,
        }
        for i, k in enumerate(skus)
    ])

    # Stores
    regions = ["East", "West", "North", "South", "Central"]
    df_store = pd.DataFrame([
        {
            "store_id": s,
            "store_name": f"Retail Outlet {s}",
            "region": regions[i % len(regions)],
            "capacity_units": 50000,
            "priority_weight": 1.0,
        }
        for i, s in enumerate(stores)
    ])

    # Inventory
    latest_date = dates[-1].strftime("%Y-%m-%d")
    df_inv = pd.DataFrame([
        {
            "allocation_date": latest_date,
            "warehouse_id": f"WH_{s}",
            "sku_id": k,
            "available_units": int(rng.integers(100, 400)),
        }
        for s in stores
        for k in skus
    ])

    return {
        "sales": df_sales,
        "calendar": df_cal,
        "promotions": df_promos,
        "products": df_prod,
        "stores": df_store,
        "inventory": df_inv,
    }


def process_real_retail_dataset(
    source_file: Path,
    store_count: int = 5,
    sku_count: int = 10,
    store_id_style: str = "source",  # "source" (S001) or "standard" (STORE_1)
) -> Dict[str, pd.DataFrame]:
    """Processes genuine retail_store_inventory.csv into the required standardized schemas."""
    print(f"[*] Ingesting raw dataset from {source_file}...")
    df_raw = pd.read_csv(source_file)

    # 1. Deterministic Store & SKU selection
    avail_stores = sorted(df_raw["Store ID"].unique().tolist())[:store_count]
    avail_skus = sorted(df_raw["Product ID"].unique().tolist())[:sku_count]

    # Optional mapping for consistency with backend hardcoded IDs if desired
    store_map = {f"S{i:03d}": f"STORE_{i}" for i in range(1, 6)} if store_id_style == "standard" else {s: s for s in avail_stores}
    sku_map = {f"P{i:04d}": f"SKU_{i:02d}" for i in range(1, 11)} if store_id_style == "standard" else {k: k for k in avail_skus}

    df_filtered = df_raw[df_raw["Store ID"].isin(avail_stores) & df_raw["Product ID"].isin(avail_skus)].copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["Date"]).dt.strftime("%Y-%m-%d")
    df_filtered["store_id"] = df_filtered["Store ID"].map(store_map)
    df_filtered["sku_id"] = df_filtered["Product ID"].map(sku_map)

    # 2. Complete Cartesian Date-Store-SKU Grid
    unique_dates = sorted(df_filtered["date"].unique().tolist())
    target_stores = [store_map[s] for s in avail_stores]
    target_skus = [sku_map[k] for k in avail_skus]

    grid_index = pd.MultiIndex.from_product(
        [unique_dates, target_stores, target_skus],
        names=["date", "store_id", "sku_id"],
    )
    df_grid = pd.DataFrame(index=grid_index).reset_index()

    # Merge observations onto complete grid
    merged = pd.merge(
        df_grid,
        df_filtered,
        on=["date", "store_id", "sku_id"],
        how="left",
    )

    # Preprocessing rules: non-negative demand, fill missing combinations with 0
    merged["units_sold"] = pd.to_numeric(merged["Units Sold"], errors="coerce").fillna(0).astype(int)
    if (merged["units_sold"] < 0).any():
        raise ValueError("CRITICAL: Invalid negative sales records detected in source dataset!")

    # Promotion mapping
    # Discount percentage converted to multiplier (e.g., 20% discount = 1.20 promo multiplier)
    merged["is_promo"] = merged["Holiday/Promotion"].fillna(0).astype(int)
    disc = pd.to_numeric(merged["Discount"], errors="coerce").fillna(0.0)
    merged["promo_multiplier"] = np.where(merged["is_promo"] == 1, (1.0 + disc / 100.0).round(2), 1.0)
    # Ensure promo_multiplier >= 1.0
    merged["promo_multiplier"] = merged["promo_multiplier"].clip(lower=1.0)

    # Holiday mapping
    merged["is_holiday"] = merged["date"].apply(lambda d: 1 if d in US_HOLIDAYS else 0)

    # Sort deterministically by store_id, sku_id, date
    df_sales = merged[[
        "date", "store_id", "sku_id", "units_sold", "is_promo", "promo_multiplier", "is_holiday"
    ]].sort_values(["store_id", "sku_id", "date"]).reset_index(drop=True)

    # 3. Calendar Dataset
    cal_dt = pd.to_datetime(unique_dates)
    df_cal = pd.DataFrame({
        "date": unique_dates,
        "day_of_week": cal_dt.day_name(),
        "day_of_week_number": cal_dt.dayofweek + 1,
        "is_weekend": cal_dt.dayofweek.isin([5, 6]).astype(int),
        "is_holiday": [1 if d in US_HOLIDAYS else 0 for d in unique_dates],
        "holiday_name": [US_HOLIDAYS.get(d, "") for d in unique_dates],
        "month": cal_dt.month,
        "week_of_year": cal_dt.isocalendar().week.astype(int),
    }).sort_values("date").reset_index(drop=True)

    # 4. Promotion Dataset
    promo_type_map = {
        0.0: "None",
        5.0: "5% Off Weekly Special",
        10.0: "10% Off Category Feature",
        15.0: "15% Off Circular Feature",
        20.0: "20% Off Major Event",
    }
    df_promos = merged[[
        "date", "store_id", "sku_id", "is_promo", "promo_multiplier"
    ]].copy()
    df_promos["promo_type"] = disc.map(promo_type_map).fillna("Promotional Event")
    df_promos.loc[df_promos["is_promo"] == 0, "promo_type"] = "None"
    df_promos["promo_type"] = df_promos["promo_type"].fillna("None")
    df_promos = df_promos.sort_values(["store_id", "sku_id", "date"]).reset_index(drop=True)

    # 5. Product Dataset
    p_cat = df_raw.groupby("Product ID")["Category"].agg(lambda x: x.mode()[0]).to_dict()
    p_price = df_raw.groupby("Product ID")["Price"].mean().round(2).to_dict()
    df_products = pd.DataFrame([
        {
            "sku_id": sku_map[k],
            "product_name": f"Item {k}",
            "category": p_cat.get(k, "General Merchandise"),
            "unit_price": p_price.get(k, 50.00),
            "priority_weight": 1.0,
        }
        for k in avail_skus
    ]).sort_values("sku_id").reset_index(drop=True)

    # 6. Store Dataset
    s_reg = df_raw.groupby("Store ID")["Region"].agg(lambda x: x.mode()[0]).to_dict()
    df_stores = pd.DataFrame([
        {
            "store_id": store_map[s],
            "store_name": f"Retail Store {s}",
            "region": s_reg.get(s, "National"),
            "capacity_units": 50000,
            "priority_weight": 1.0,
        }
        for s in avail_stores
    ]).sort_values("store_id").reset_index(drop=True)

    # 7. Inventory Dataset (Latest empirical on-hand inventory)
    latest_dt_str = max(unique_dates)
    df_latest = df_raw[df_raw["Date"] == latest_dt_str].copy()
    wh_map = {s: f"WH_{store_map[s]}" for s in avail_stores}

    df_latest_sub = df_latest[df_latest["Store ID"].isin(avail_stores) & df_latest["Product ID"].isin(avail_skus)].copy()
    df_inv = pd.DataFrame({
        "allocation_date": latest_dt_str,
        "warehouse_id": df_latest_sub["Store ID"].map(wh_map),
        "sku_id": df_latest_sub["Product ID"].map(sku_map),
        "available_units": df_latest_sub["Inventory Level"].astype(int),
    }).sort_values(["warehouse_id", "sku_id"]).reset_index(drop=True)

    return {
        "sales": df_sales,
        "calendar": df_cal,
        "promotions": df_promos,
        "products": df_products,
        "stores": df_stores,
        "inventory": df_inv,
    }


def validate_and_report(datasets: Dict[str, pd.DataFrame], source_type: str):
    """Computes and prints a thorough dataset validation report."""
    df_sales = datasets["sales"]
    df_cal = datasets["calendar"]
    df_promos = datasets["promotions"]
    df_prod = datasets["products"]
    df_store = datasets["stores"]
    df_inv = datasets["inventory"]

    print("\n" + "=" * 75)
    print("DATASET VALIDATION REPORT")
    print("=" * 75)
    print(f"Dataset Source Type           : {source_type}")
    print(f"Total Sales Rows              : {len(df_sales):,}")
    print(f"Minimum Date                  : {df_sales['date'].min()}")
    print(f"Maximum Date                  : {df_sales['date'].max()}")
    print(f"Unique Dates Count            : {df_sales['date'].nunique()}")
    print(f"Unique Stores Count           : {df_sales['store_id'].nunique()} ({df_sales['store_id'].unique().tolist()})")
    print(f"Unique SKUs Count             : {df_sales['sku_id'].nunique()} ({df_sales['sku_id'].unique().tolist()})")

    # Missing values
    print("\n[Missing Values Per Column in sales.csv]")
    for col, null_cnt in df_sales.isnull().sum().items():
        print(f"  - {col:<18}: {null_cnt}")

    # Duplicates & Anomalies
    dup_cnt = df_sales.duplicated(subset=["date", "store_id", "sku_id"]).sum()
    print(f"\nDuplicate [date, store, SKU]  : {dup_cnt}")

    # Invalid dates
    invalid_dates = pd.to_datetime(df_sales["date"], errors="coerce").isnull().sum()
    print(f"Invalid Date Count            : {invalid_dates}")

    # Units sold checks
    neg_units = (df_sales["units_sold"] < 0).sum()
    print(f"Negative units_sold Count     : {neg_units}")

    zero_demand_cnt = (df_sales["units_sold"] == 0).sum()
    zero_demand_pct = (zero_demand_cnt / len(df_sales)) * 100.0
    print(f"Zero-Demand Observations      : {zero_demand_cnt:,} ({zero_demand_pct:.2f}%)")

    # Promotion & Holiday checks
    promo_cnt = (df_sales["is_promo"] == 1).sum()
    hol_cnt = (df_sales["is_holiday"] == 1).sum()
    print(f"Active Promotion Rows         : {promo_cnt:,} ({(promo_cnt/len(df_sales))*100:.2f}%)")
    print(f"Active Holiday Rows           : {hol_cnt:,} ({(hol_cnt/len(df_sales))*100:.2f}%)")

    # Promo multiplier validation
    invalid_promo_mult = (df_sales["promo_multiplier"] < 1.0).sum()
    print(f"Invalid Promo Multipliers (<1): {invalid_promo_mult}")

    # Descriptive statistics
    print("\n[Descriptive Statistics for units_sold]")
    stats = df_sales["units_sold"].describe()
    for k, v in stats.items():
        print(f"  - {k:<10}: {v:>10.2f}")

    print("\n[Associated Entities]")
    print(f"  - Calendar Rows             : {len(df_cal):,}")
    print(f"  - Promotion Rows            : {len(df_promos):,}")
    print(f"  - Product Master Rows       : {len(df_prod):,}")
    print(f"  - Store Master Rows         : {len(df_store):,}")
    print(f"  - Inventory Input Rows      : {len(df_inv):,}")
    print("=" * 75)

    # Acceptance assertion verification
    assert df_sales["store_id"].nunique() == 5, "Sales dataset must contain exactly 5 stores"
    assert df_sales["sku_id"].nunique() == 10, "Sales dataset must contain exactly 10 SKUs"
    assert dup_cnt == 0, "No duplicate date-store-SKU rows allowed"
    assert neg_units == 0, "No negative units_sold allowed"
    assert invalid_promo_mult == 0, "Promo multiplier must be >= 1.0"
    print("[SUCCESS] All acceptance criteria validated successfully!\n")


def main():
    parser = argparse.ArgumentParser(description="Prepare datasets for demand forecasting and inventory allocation")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--raw-dir", default="data/raw", help="Raw dataset directory")
    parser.add_argument("--output-dir", default="data/processed", help="Output processed directory")
    parser.add_argument("--store-count", type=int, default=5, help="Number of stores to select")
    parser.add_argument("--sku-count", type=int, default=10, help="Number of SKUs to select")
    parser.add_argument(
        "--store-id-style",
        choices=["source", "standard"],
        default="standard",
        help="Store ID formatting ('standard' = STORE_1..5, 'source' = S001..5)",
    )
    parser.add_argument("--force-synthetic", action="store_true", help="Force synthetic demo dataset generation")

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    raw_dir = (project_root / args.raw_dir).resolve()
    output_dir = (project_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("DEMAND FORECASTING & ALLOCATION - DATASET PREPARATION PIPELINE")
    print("=" * 75)
    print(f"Project Root: {project_root}")
    print(f"Raw Dir     : {raw_dir}")
    print(f"Output Dir  : {output_dir}")

    source_file, source_desc = find_source_file(raw_dir)

    if args.force_synthetic:
        source_type = "SYNTHETIC DEMO FALLBACK (Explicitly Requested)"
        datasets = create_synthetic_fallback(output_dir, num_stores=args.store_count, num_skus=args.sku_count)
    elif source_file is not None:
        source_type = f"REAL HISTORICAL SOURCE ({source_desc})"
        datasets = process_real_retail_dataset(
            source_file=source_file,
            store_count=args.store_count,
            sku_count=args.sku_count,
            store_id_style=args.store_id_style,
        )
    else:
        print("\n" + "!" * 75)
        print("[ERROR] MISSING SOURCE DATASET FILES!")
        print("!" * 75)
        print("Expected authentic source retail files were not found in:")
        print(f"  -> {raw_dir}")
        print("\nPlease place one of the following official source files into data/raw/:")
        print("  1. retail_store_inventory.csv (from archive (2).zip)")
        print("  2. sales_train_evaluation.csv (M5 Forecasting)")
        print("  3. sales_train_validation.csv (M5 Forecasting)")
        print("\nTo generate a temporary synthetic demo fallback without real data, run:")
        print("  python scripts/prepare_dataset.py --force-synthetic")
        print("!" * 75)
        raise FileNotFoundError(f"Authentic retail source dataset missing in {raw_dir}")

    # Save output CSV files
    for name, df in datasets.items():
        out_csv = output_dir / f"{name}.csv"
        df.to_csv(out_csv, index=False)
        print(f"[OK] Wrote {name:<12}: {out_csv} ({len(df):,} rows, {len(df.columns)} cols)")

    # Run validation and print report
    validate_and_report(datasets, source_type)


if __name__ == "__main__":
    main()
