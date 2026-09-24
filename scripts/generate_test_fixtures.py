"""
scripts/generate_test_fixtures.py
---------------------------------
Generates deterministic testing fixtures for the forecasting and allocation pipeline.
All generated fixtures are synthetic test data, clearly labelled, with fixed seeds
and companion metadata.

Also provides comprehensive automated validation for each fixture against:
- backend.data_loader
- backend.forecasting
- backend.allocation
"""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import numpy as np

from backend.data_loader import load_demand_data
from backend.forecasting import forecast_demand
from backend.allocation import allocate_inventory, get_allocation_summary

# Set deterministic random seed
np.random.seed(42)


def generate_normal_demand(output_dir: Path) -> Path:
    """Fixture 1: normal_demand.csv
    Demand can be fully satisfied.
    Expected: Full allocation, Zero shortage, Positive remaining inventory.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_1", "STORE_2", "STORE_3"]
    skus = ["SKU_01", "SKU_02"]

    records = []
    for d in dates:
        for s in stores:
            for k in skus:
                records.append({
                    "date": d,
                    "store_id": s,
                    "sku_id": k,
                    "units_sold": 10.0,
                    "is_promo": 0,
                    "promo_multiplier": 1.0,
                    "is_holiday": 0,
                    "data_type": "SYNTHETIC_TEST_DATA",
                })

    df = pd.DataFrame(records)
    file_path = output_dir / "normal_demand.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_shortage_case(output_dir: Path) -> Path:
    """Fixture 2: shortage_case.csv
    Demand: STORE_A = 500, STORE_B = 400, STORE_C = 300.
    Companion config: Available inventory = 1000.
    Expected: Allocation ~ [417, 333, 250], Total shortage = 200.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    demand_map = {"STORE_A": 500.0, "STORE_B": 400.0, "STORE_C": 300.0}

    records = []
    for d in dates:
        for s, d_val in demand_map.items():
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": d_val,
                "is_promo": 0,
                "promo_multiplier": 1.0,
                "is_holiday": 0,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "shortage_case.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_promotion_case(output_dir: Path) -> Path:
    """Fixture 3: promotion_case.csv
    Historical baseline with STORE_B promotion multiplier = 1.30.
    Expected: STORE_B forecast increases by 30%, other stores remain unchanged.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B", "STORE_C"]

    records = []
    for d in dates:
        for s in stores:
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": 100.0,
                "is_promo": 1 if s == "STORE_B" else 0,
                "promo_multiplier": 1.30 if s == "STORE_B" else 1.0,
                "is_holiday": 0,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "promotion_case.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_holiday_case(output_dir: Path) -> Path:
    """Fixture 4: holiday_case.csv
    Expected: Adjusted forecast equals baseline multiplied by 1.15.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B"]

    records = []
    for d in dates:
        for s in stores:
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": 100.0,
                "is_promo": 0,
                "promo_multiplier": 1.0,
                "is_holiday": 1,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "holiday_case.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_promotion_and_holiday_case(output_dir: Path) -> Path:
    """Fixture 5: promotion_and_holiday_case.csv
    Expected: Both promotion multiplier (1.30 on STORE_B) and holiday (1.15) applied.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B"]

    records = []
    for d in dates:
        for s in stores:
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": 100.0,
                "is_promo": 1 if s == "STORE_B" else 0,
                "promo_multiplier": 1.30 if s == "STORE_B" else 1.0,
                "is_holiday": 1,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "promotion_and_holiday_case.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_zero_demand(output_dir: Path) -> Path:
    """Fixture 6: zero_demand.csv
    Expected: Zero allocation, Zero shortage, No division-by-zero error.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B"]

    records = []
    for d in dates:
        for s in stores:
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": 0.0,
                "is_promo": 0,
                "promo_multiplier": 1.0,
                "is_holiday": 0,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "zero_demand.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_zero_inventory(output_dir: Path) -> Path:
    """Fixture 7: zero_inventory.csv
    Expected: All allocations are zero, shortage equals total demand.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B"]

    records = []
    for d in dates:
        for s in stores:
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": 50.0,
                "is_promo": 0,
                "promo_multiplier": 1.0,
                "is_holiday": 0,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "zero_inventory.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_missing_dates(output_dir: Path) -> Path:
    """Fixture 8: missing_dates.csv
    Remove selected dates from store-SKU groups.
    Expected: Loader completes the date grid and missing units_sold becomes 0.
    """
    dates = pd.date_range("2023-01-01", periods=7, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B"]
    skus = ["SKU_01", "SKU_02"]

    records = []
    for d in dates:
        for s in stores:
            for k in skus:
                # Omit specific combinations to simulate missing records
                if s == "STORE_A" and k == "SKU_01" and d in ["2023-01-02", "2023-01-05"]:
                    continue
                if s == "STORE_B" and k == "SKU_02" and d == "2023-01-03":
                    continue

                records.append({
                    "date": d,
                    "store_id": s,
                    "sku_id": k,
                    "units_sold": 25.0,
                    "is_promo": 0,
                    "promo_multiplier": 1.0,
                    "is_holiday": 0,
                    "data_type": "SYNTHETIC_TEST_DATA",
                })

    df = pd.DataFrame(records)
    file_path = output_dir / "missing_dates.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_short_history(output_dir: Path) -> Path:
    """Fixture 9: short_history.csv
    Include groups with fewer than 7 observations.
    Expected: Cold-start fallback is triggered; no NaN values in forecast.
    """
    records = [
        # STORE_A with only 3 observations
        {"date": "2023-01-05", "store_id": "STORE_A", "sku_id": "SKU_01", "units_sold": 12.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        {"date": "2023-01-06", "store_id": "STORE_A", "sku_id": "SKU_01", "units_sold": 15.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        {"date": "2023-01-07", "store_id": "STORE_A", "sku_id": "SKU_01", "units_sold": 18.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        # STORE_B with 5 observations
        {"date": "2023-01-03", "store_id": "STORE_B", "sku_id": "SKU_01", "units_sold": 20.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        {"date": "2023-01-04", "store_id": "STORE_B", "sku_id": "SKU_01", "units_sold": 22.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        {"date": "2023-01-05", "store_id": "STORE_B", "sku_id": "SKU_01", "units_sold": 25.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        {"date": "2023-01-06", "store_id": "STORE_B", "sku_id": "SKU_01", "units_sold": 24.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
        {"date": "2023-01-07", "store_id": "STORE_B", "sku_id": "SKU_01", "units_sold": 28.0, "is_promo": 0, "promo_multiplier": 1.0, "is_holiday": 0, "data_type": "SYNTHETIC_TEST_DATA"},
    ]

    df = pd.DataFrame(records)
    file_path = output_dir / "short_history.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_invalid_records(output_dir: Path) -> Path:
    """Fixture 10: invalid_records.csv
    Include separate invalid records for:
    - Invalid date
    - Negative sales
    - Missing store ID
    - Missing SKU ID
    - Duplicate date-store-SKU
    - Text in numeric column
    Expected: Loader rejects each invalid record type with a specific ValueError.
    """
    records = [
        # Baseline valid row
        {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": "10", "defect_type": "valid_baseline"},
        # 1. Invalid date
        {"date": "2023-99-99", "store_id": "STORE_1", "sku_id": "SKU_02", "units_sold": "10", "defect_type": "invalid_date"},
        # 2. Negative sales
        {"date": "2023-01-02", "store_id": "STORE_1", "sku_id": "SKU_03", "units_sold": "-15", "defect_type": "negative_units_sold"},
        # 3. Missing store ID
        {"date": "2023-01-02", "store_id": "", "sku_id": "SKU_04", "units_sold": "10", "defect_type": "missing_store_id"},
        # 4. Missing SKU ID
        {"date": "2023-01-02", "store_id": "STORE_2", "sku_id": "", "units_sold": "10", "defect_type": "missing_sku_id"},
        # 5. Duplicate date-store-SKU
        {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": "20", "defect_type": "duplicate_key"},
        # 6. Text in numeric column
        {"date": "2023-01-03", "store_id": "STORE_3", "sku_id": "SKU_05", "units_sold": "twenty_five", "defect_type": "text_in_numeric"},
    ]

    df = pd.DataFrame(records)
    file_path = output_dir / "invalid_records.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_rounding_case(output_dir: Path) -> Path:
    """Fixture 11: rounding_case.csv
    Demand: STORE_A = 1, STORE_B = 1, STORE_C = 1.
    Inventory: 2.
    Expected: Total allocation exactly 2, no store receives > 1, result is deterministic.
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    stores = ["STORE_A", "STORE_B", "STORE_C"]

    records = []
    for d in dates:
        for s in stores:
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": 1.0,
                "is_promo": 0,
                "promo_multiplier": 1.0,
                "is_holiday": 0,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "rounding_case.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_dominant_store_case(output_dir: Path) -> Path:
    """Fixture 12: dominant_store_case.csv
    Demand: STORE_A = 1000, STORE_B = 1, STORE_C = 1.
    Inventory: 500 (limited).
    Expected: Proportional allocation, non-negative, stays within supply (total <= 500).
    """
    dates = pd.date_range("2023-01-01", periods=14, freq="D").strftime("%Y-%m-%d")
    demand_map = {"STORE_A": 1000.0, "STORE_B": 1.0, "STORE_C": 1.0}

    records = []
    for d in dates:
        for s, d_val in demand_map.items():
            records.append({
                "date": d,
                "store_id": s,
                "sku_id": "SKU_01",
                "units_sold": d_val,
                "is_promo": 0,
                "promo_multiplier": 1.0,
                "is_holiday": 0,
                "data_type": "SYNTHETIC_TEST_DATA",
            })

    df = pd.DataFrame(records)
    file_path = output_dir / "dominant_store_case.csv"
    df.to_csv(file_path, index=False)
    return file_path


def generate_companion_metadata(output_dir: Path) -> Path:
    """Creates companion JSON metadata for fixtures with specific parameters."""
    metadata = {
        "fixtures": {
            "normal_demand.csv": {
                "purpose": "Full fulfillment test case",
                "available_inventory": 1000,
                "horizon_days": 7,
                "is_holiday_week": False,
                "promo_boost": None,
                "expected": {
                    "total_shortage": 0.0,
                    "remaining_inventory_gt_zero": True,
                },
            },
            "shortage_case.csv": {
                "purpose": "Proportional scarcity allocation test case (Worked Example)",
                "available_inventory": 1000,
                "horizon_days": 1,
                "is_holiday_week": False,
                "promo_boost": None,
                "expected": {
                    "STORE_A_allocated": 417,
                    "STORE_B_allocated": 333,
                    "STORE_C_allocated": 250,
                    "total_shortage": 200.0,
                    "remaining_inventory": 0.0,
                },
            },
            "promotion_case.csv": {
                "purpose": "Targeted promotion test case",
                "available_inventory": 3000,
                "horizon_days": 7,
                "is_holiday_week": False,
                "promo_boost": {"STORE_B": 1.30},
                "expected": {
                    "STORE_B_uplift_pct": 30.0,
                    "other_stores_unchanged": True,
                },
            },
            "holiday_case.csv": {
                "purpose": "Holiday uplift test case (+15% across all stores)",
                "available_inventory": 2000,
                "horizon_days": 7,
                "is_holiday_week": True,
                "promo_boost": None,
                "expected": {
                    "all_stores_uplift_multiplier": 1.15,
                },
            },
            "promotion_and_holiday_case.csv": {
                "purpose": "Combined marketing promotion and holiday uplift",
                "available_inventory": 2500,
                "horizon_days": 7,
                "is_holiday_week": True,
                "promo_boost": {"STORE_B": 1.30},
                "expected": {
                    "STORE_B_combined_multiplier": 1.495,
                    "STORE_A_holiday_multiplier": 1.15,
                },
            },
            "zero_demand.csv": {
                "purpose": "Zero demand boundary condition",
                "available_inventory": 500,
                "horizon_days": 7,
                "is_holiday_week": False,
                "promo_boost": None,
                "expected": {
                    "total_demand": 0.0,
                    "total_allocated": 0.0,
                    "total_shortage": 0.0,
                    "remaining_inventory": 500.0,
                },
            },
            "zero_inventory.csv": {
                "purpose": "Zero inventory boundary condition",
                "available_inventory": 0,
                "horizon_days": 7,
                "is_holiday_week": False,
                "promo_boost": None,
                "expected": {
                    "total_allocated": 0.0,
                    "shortage_equals_demand": True,
                },
            },
            "missing_dates.csv": {
                "purpose": "Grid completion and missing observation filling",
                "expected_grid_size": 28,
                "missing_filled_with_zero": True,
            },
            "short_history.csv": {
                "purpose": "Cold-start fallback for series under 7 observations",
                "horizon_days": 7,
                "expected": {
                    "no_nan_values": True,
                    "fallback_triggered": True,
                },
            },
            "invalid_records.csv": {
                "purpose": "Negative data loader rejection validation",
                "defects_tested": [
                    "invalid_date",
                    "negative_units_sold",
                    "missing_store_id",
                    "missing_sku_id",
                    "duplicate_key",
                    "text_in_numeric",
                ],
            },
            "rounding_case.csv": {
                "purpose": "Discrete largest-remainder integer distribution with ties",
                "available_inventory": 2,
                "horizon_days": 1,
                "expected": {
                    "total_allocated": 2,
                    "max_store_allocation": 1,
                    "deterministic": True,
                },
            },
            "dominant_store_case.csv": {
                "purpose": "Extreme demand skew allocation under inventory scarcity",
                "available_inventory": 500,
                "horizon_days": 1,
                "expected": {
                    "total_allocated": 500,
                    "no_negative_allocations": True,
                    "STORE_A_allocation_within_supply": True,
                },
            },
        }
    }
    meta_path = output_dir / "fixtures_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    return meta_path


def generate_manifest_readme(output_dir: Path) -> Path:
    """Creates the fixture manifest README.md under data/test_fixtures/."""
    content = """# Test Fixtures Manifest

All files in this directory are **deterministic synthetic test fixtures** created for unit testing, integration verification, and pipeline regression testing for the **Inventory-Constrained Demand Forecasting & Allocation** system.

> [!NOTE]
> All fixtures are clearly designated with synthetic metadata labels (`data_type="SYNTHETIC_TEST_DATA"`). No production or confidential data is contained herein.

---

## Fixture Catalog

| # | Fixture Filename | Pipeline Target | Primary Purpose | Input Conditions | Expected Outcome |
|---|---|---|---|---|---|
| **1** | [`normal_demand.csv`](./normal_demand.csv) | End-to-End | Normal demand with abundant supply | 3 stores, 2 SKUs, 14 days; supply = 1,000 units | Full allocation, 0 shortage, positive remaining inventory |
| **2** | [`shortage_case.csv`](./shortage_case.csv) | Allocation | Proportional allocation under scarcity (Worked Example) | STORE_A: 500, STORE_B: 400, STORE_C: 300; supply = 1,000 | Allocation: [417, 333, 250], total shortage = 200 |
| **3** | [`promotion_case.csv`](./promotion_case.csv) | Forecasting | Targeted store promotion adjustment | STORE_B promo multiplier = 1.30; stores A, B, C baseline = 100/day | STORE_B forecast lifts +30%; STORE_A and STORE_C unchanged |
| **4** | [`holiday_case.csv`](./holiday_case.csv) | Forecasting | Universal holiday demand adjustment | Holiday week toggle active; baseline = 100/day | All store forecasts uplifted by exactly +15% (1.15 multiplier) |
| **5** | [`promotion_and_holiday_case.csv`](./promotion_and_holiday_case.csv) | Forecasting | Interaction of promotion and holiday uplifts | STORE_B promo (1.30x) + holiday week (1.15x) | Multiplicative combination (1.495x for STORE_B, 1.15x for STORE_A) |
| **6** | [`zero_demand.csv`](./zero_demand.csv) | Forecasting / Allocation | Zero historical demand edge case | All historical units_sold = 0; supply = 500 | 0 allocation, 0 shortage, remaining = 500, no division-by-zero |
| **7** | [`zero_inventory.csv`](./zero_inventory.csv) | Allocation | Zero available inventory edge case | Normal demand; available inventory = 0 | All store allocations = 0; total shortage equals total demand |
| **8** | [`missing_dates.csv`](./missing_dates.csv) | Data Loader | Date grid completion & imputation | Incomplete store-SKU-date observations | Loader completes full Cartesian grid (28 rows) and imputes missing units as 0 |
| **9** | [`short_history.csv`](./short_history.csv) | Forecasting | Cold-start handling for sparse series | Stores with < 7 historical observations | Cold-start fallback calculates mean; zero NaNs or infs in forecast |
| **10** | [`invalid_records.csv`](./invalid_records.csv) | Data Loader | Negative schema validation & error handling | Invalid dates, negative units, blank IDs, duplicates, text values | Loader rejects each defect with a precise, informative `ValueError` |
| **11** | [`rounding_case.csv`](./rounding_case.csv) | Allocation | Discrete largest-remainder integer tie-breaking | STORE_A: 1, STORE_B: 1, STORE_C: 1; inventory = 2 | Allocation sum exactly 2; no store > 1; deterministic distribution |
| **12** | [`dominant_store_case.csv`](./dominant_store_case.csv) | Allocation | Extreme demand skew under severe inventory cap | STORE_A: 1000, STORE_B: 1, STORE_C: 1; inventory = 500 | Quota allocated proportionally; strictly non-negative; total == 500 |

---

## Machine-Readable Specification

See [`fixtures_metadata.json`](./fixtures_metadata.json) for structured parameter bindings, forecast horizons, inventory levels, and expected allocation results for automated test harnesses.
"""
    manifest_path = output_dir / "README.md"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(content)
    return manifest_path


def validate_fixtures(output_dir: Path) -> Dict[str, Any]:
    """Validates every generated fixture against the data loader, forecaster, and allocation engine."""
    results = {}

    # 1. Normal demand
    f1 = load_demand_data(output_dir / "normal_demand.csv")
    fc1 = forecast_demand(f1, horizon_days=7)
    al1 = allocate_inventory(fc1, total_available_units=1000)
    s1 = al1.attrs["summary"]
    assert s1["total_shortage"] == 0.0, "normal_demand shortage should be 0"
    assert s1["remaining_inventory"] > 0, "normal_demand should have positive remaining inventory"
    results["normal_demand.csv"] = {
        "rows": len(f1),
        "status": "VALIDATED",
        "demand": s1["total_forecasted_demand"],
        "allocated": s1["total_allocated_units"],
        "shortage": s1["total_shortage"],
    }

    # 2. Shortage case (Worked Example)
    f2 = load_demand_data(output_dir / "shortage_case.csv")
    fc2 = forecast_demand(f2, horizon_days=1)
    al2 = allocate_inventory(fc2, total_available_units=1000)
    s2 = al2.attrs["summary"]
    alloc_map = dict(zip(al2["store_id"], al2["allocated_units"]))
    assert alloc_map["STORE_A"] == 417, f"STORE_A expected 417, got {alloc_map['STORE_A']}"
    assert alloc_map["STORE_B"] == 333, f"STORE_B expected 333, got {alloc_map['STORE_B']}"
    assert alloc_map["STORE_C"] == 250, f"STORE_C expected 250, got {alloc_map['STORE_C']}"
    assert s2["total_shortage"] == 200.0, f"Expected 200 shortage, got {s2['total_shortage']}"
    results["shortage_case.csv"] = {
        "rows": len(f2),
        "status": "VALIDATED",
        "allocations": alloc_map,
        "shortage": s2["total_shortage"],
    }

    # 3. Promotion case
    f3 = load_demand_data(output_dir / "promotion_case.csv")
    fc3_base = forecast_demand(f3, horizon_days=7, promo_boost=None)
    fc3_promo = forecast_demand(f3, horizon_days=7, promo_boost={"STORE_B": 1.30})
    b_base = fc3_base[fc3_base["store_id"] == "STORE_B"]["predicted_units"].sum()
    b_promo = fc3_promo[fc3_promo["store_id"] == "STORE_B"]["predicted_units"].sum()
    a_base = fc3_base[fc3_base["store_id"] == "STORE_A"]["predicted_units"].sum()
    a_promo = fc3_promo[fc3_promo["store_id"] == "STORE_A"]["predicted_units"].sum()
    assert round(b_promo / b_base, 2) == 1.30, "STORE_B promo did not scale by 1.30"
    assert a_base == a_promo, "STORE_A should be unchanged by STORE_B promotion"
    results["promotion_case.csv"] = {
        "rows": len(f3),
        "status": "VALIDATED",
        "store_b_base": b_base,
        "store_b_promo": b_promo,
        "store_a_unchanged": True,
    }

    # 4. Holiday case
    f4 = load_demand_data(output_dir / "holiday_case.csv")
    fc4_base = forecast_demand(f4, horizon_days=7, is_holiday_week=False)
    fc4_hol = forecast_demand(f4, horizon_days=7, is_holiday_week=True)
    d_base = fc4_base["predicted_units"].sum()
    d_hol = fc4_hol["predicted_units"].sum()
    assert round(d_hol / d_base, 2) == 1.15, "Holiday uplift was not 1.15"
    results["holiday_case.csv"] = {
        "rows": len(f4),
        "status": "VALIDATED",
        "baseline_demand": d_base,
        "holiday_demand": d_hol,
        "multiplier": round(d_hol / d_base, 2),
    }

    # 5. Promotion and holiday case
    f5 = load_demand_data(output_dir / "promotion_and_holiday_case.csv")
    fc5_base = forecast_demand(f5, horizon_days=7, promo_boost=None, is_holiday_week=False)
    fc5_both = forecast_demand(f5, horizon_days=7, promo_boost={"STORE_B": 1.30}, is_holiday_week=True)
    b5_base = fc5_base[fc5_base["store_id"] == "STORE_B"]["predicted_units"].sum()
    b5_both = fc5_both[fc5_both["store_id"] == "STORE_B"]["predicted_units"].sum()
    assert round(b5_both / b5_base, 3) == round(1.30 * 1.15, 3), "Both multipliers not applied"
    results["promotion_and_holiday_case.csv"] = {
        "rows": len(f5),
        "status": "VALIDATED",
        "store_b_multiplier": round(b5_both / b5_base, 3),
    }

    # 6. Zero demand
    f6 = load_demand_data(output_dir / "zero_demand.csv")
    fc6 = forecast_demand(f6, horizon_days=7)
    al6 = allocate_inventory(fc6, total_available_units=500)
    s6 = al6.attrs["summary"]
    assert s6["total_allocated_units"] == 0.0
    assert s6["total_shortage"] == 0.0
    results["zero_demand.csv"] = {
        "rows": len(f6),
        "status": "VALIDATED",
        "allocated": 0.0,
        "shortage": 0.0,
    }

    # 7. Zero inventory
    f7 = load_demand_data(output_dir / "zero_inventory.csv")
    fc7 = forecast_demand(f7, horizon_days=7)
    al7 = allocate_inventory(fc7, total_available_units=0)
    s7 = al7.attrs["summary"]
    assert s7["total_allocated_units"] == 0.0
    assert s7["total_shortage"] == s7["total_forecasted_demand"]
    results["zero_inventory.csv"] = {
        "rows": len(f7),
        "status": "VALIDATED",
        "allocated": 0.0,
        "shortage_equals_demand": True,
    }

    # 8. Missing dates
    # Raw file has 25 rows
    df_raw8 = pd.read_csv(output_dir / "missing_dates.csv")
    f8 = load_demand_data(output_dir / "missing_dates.csv")
    assert len(f8) == 28, f"Expected grid 28 rows, got {len(f8)}"
    missing_count = (f8["units_sold"] == 0.0).sum()
    assert missing_count == 3, f"Expected 3 filled zeroes, got {missing_count}"
    results["missing_dates.csv"] = {
        "raw_rows": len(df_raw8),
        "completed_rows": len(f8),
        "status": "VALIDATED",
        "imputed_zeroes": int(missing_count),
    }

    # 9. Short history
    f9 = load_demand_data(output_dir / "short_history.csv")
    fc9 = forecast_demand(f9, horizon_days=7)
    assert not fc9["predicted_units"].isnull().any(), "Short history produced NaNs"
    assert (fc9["predicted_units"] > 0).all(), "Short history produced non-positive forecasts"
    results["short_history.csv"] = {
        "rows": len(f9),
        "status": "VALIDATED",
        "no_nan": True,
        "forecast_stores": sorted(fc9["store_id"].unique().tolist()),
    }

    # 10. Invalid records (test each defect type)
    df_inv = pd.read_csv(output_dir / "invalid_records.csv")
    defect_results = {}
    for defect in ["invalid_date", "negative_units_sold", "missing_store_id", "missing_sku_id", "duplicate_key", "text_in_numeric"]:
        subset = df_inv[df_inv["defect_type"].isin(["valid_baseline", defect])][["date", "store_id", "sku_id", "units_sold"]]
        tmp_path = output_dir / f"_tmp_{defect}.csv"
        subset.to_csv(tmp_path, index=False)
        rejected = False
        err_msg = ""
        try:
            load_demand_data(tmp_path)
        except ValueError as exc:
            rejected = True
            err_msg = str(exc)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
        assert rejected, f"Failed to reject defect: {defect}"
        defect_results[defect] = f"REJECTED: {err_msg[:60]}..."
    results["invalid_records.csv"] = {
        "rows": len(df_inv),
        "status": "VALIDATED",
        "defect_tests": defect_results,
    }

    # 11. Rounding case
    f11 = load_demand_data(output_dir / "rounding_case.csv")
    fc11 = forecast_demand(f11, horizon_days=1)
    al11 = allocate_inventory(fc11, total_available_units=2)
    s11 = al11.attrs["summary"]
    assert s11["total_allocated_units"] == 2.0
    assert (al11["allocated_units"] <= 1).all()
    results["rounding_case.csv"] = {
        "rows": len(f11),
        "status": "VALIDATED",
        "allocated_sum": s11["total_allocated_units"],
        "max_alloc": int(al11["allocated_units"].max()),
    }

    # 12. Dominant store case
    f12 = load_demand_data(output_dir / "dominant_store_case.csv")
    fc12 = forecast_demand(f12, horizon_days=1)
    al12 = allocate_inventory(fc12, total_available_units=500)
    s12 = al12.attrs["summary"]
    assert s12["total_allocated_units"] == 500.0
    assert (al12["allocated_units"] >= 0).all()
    results["dominant_store_case.csv"] = {
        "rows": len(f12),
        "status": "VALIDATED",
        "allocated_sum": s12["total_allocated_units"],
        "min_alloc": int(al12["allocated_units"].min()),
    }

    return results


def generate_all_fixtures():
    """Generates all 12 fixtures, companion metadata, manifest README, and runs full validation."""
    root = Path(__file__).resolve().parent.parent
    fixtures_dir = root / "data" / "test_fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("GENERATING DETERMINISTIC TEST FIXTURES FOR PIPELINE")
    print(f"Target Directory: {fixtures_dir}")
    print("=" * 75)

    files_created = [
        generate_normal_demand(fixtures_dir),
        generate_shortage_case(fixtures_dir),
        generate_promotion_case(fixtures_dir),
        generate_holiday_case(fixtures_dir),
        generate_promotion_and_holiday_case(fixtures_dir),
        generate_zero_demand(fixtures_dir),
        generate_zero_inventory(fixtures_dir),
        generate_missing_dates(fixtures_dir),
        generate_short_history(fixtures_dir),
        generate_invalid_records(fixtures_dir),
        generate_rounding_case(fixtures_dir),
        generate_dominant_store_case(fixtures_dir),
    ]

    for p in files_created:
        row_cnt = len(pd.read_csv(p))
        print(f"[OK] Generated: {p.name:<32} ({row_cnt:>4} rows)")

    meta_file = generate_companion_metadata(fixtures_dir)
    print(f"[OK] Generated companion metadata: {meta_file.name}")

    readme_file = generate_manifest_readme(fixtures_dir)
    print(f"[OK] Generated fixture manifest:   {readme_file.name}")

    print("\n" + "=" * 75)
    print("RUNNING AUTOMATED VALIDATION ON ALL 12 FIXTURES")
    print("=" * 75)
    val_results = validate_fixtures(fixtures_dir)
    for fname, info in val_results.items():
        print(f"[OK] Validated {fname:<30}: {info['status']}")

    print("\nAll 12 test fixtures successfully generated, validated, and manifested.")


if __name__ == "__main__":
    generate_all_fixtures()
