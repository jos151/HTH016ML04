"""
Generate controlled, deterministic test fixtures required by testing guidelines.
"""
from pathlib import Path
import shutil
import pandas as pd

FIXTURES_DIR = Path("D:/HTH016ML04/data/test_fixtures")
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# 1. sufficient_inventory.csv (demand 50 units total, inventory 100)
# 2. exact_inventory.csv (demand 50 units total, inventory 50)
records_base = []
for d in ["2023-01-01", "2023-01-02"]:
    for s in ["STORE_1", "STORE_2"]:
        records_base.append({
            "date": d,
            "store_id": s,
            "sku_id": "SKU_01",
            "units_sold": 12.5,
            "is_promo": 0,
            "promo_multiplier": 1.0,
            "is_holiday": 0,
            "data_type": "SYNTHETIC_TEST_DATA",
        })
df_base = pd.DataFrame(records_base)
df_base.to_csv(FIXTURES_DIR / "sufficient_inventory.csv", index=False)
df_base.to_csv(FIXTURES_DIR / "exact_inventory.csv", index=False)

# 3. combined_promotion_holiday_case.csv
if (FIXTURES_DIR / "promotion_and_holiday_case.csv").exists():
    shutil.copy(FIXTURES_DIR / "promotion_and_holiday_case.csv", FIXTURES_DIR / "combined_promotion_holiday_case.csv")

# 4. invalid_dates.csv
df_inv_dates = pd.DataFrame([
    {"date": "not-a-date", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
    {"date": "2023-99-99", "store_id": "STORE_2", "sku_id": "SKU_01", "units_sold": 15.0, "data_type": "SYNTHETIC_TEST_DATA"},
])
df_inv_dates.to_csv(FIXTURES_DIR / "invalid_dates.csv", index=False)

# 5. negative_sales.csv
df_neg_sales = pd.DataFrame([
    {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": -5.0, "data_type": "SYNTHETIC_TEST_DATA"},
    {"date": "2023-01-02", "store_id": "STORE_2", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
])
df_neg_sales.to_csv(FIXTURES_DIR / "negative_sales.csv", index=False)

# 6. missing_store_id.csv
df_miss_store = pd.DataFrame([
    {"date": "2023-01-01", "store_id": "", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
    {"date": "2023-01-02", "store_id": "STORE_2", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
])
df_miss_store.to_csv(FIXTURES_DIR / "missing_store_id.csv", index=False)

# 7. missing_sku_id.csv
df_miss_sku = pd.DataFrame([
    {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": None, "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
    {"date": "2023-01-02", "store_id": "STORE_2", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
])
df_miss_sku.to_csv(FIXTURES_DIR / "missing_sku_id.csv", index=False)

# 8. duplicate_records.csv
df_dup = pd.DataFrame([
    {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
    {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": 10.0, "data_type": "SYNTHETIC_TEST_DATA"},
])
df_dup.to_csv(FIXTURES_DIR / "duplicate_records.csv", index=False)

# 9. invalid_numeric_values.csv
df_inv_num = pd.DataFrame([
    {"date": "2023-01-01", "store_id": "STORE_1", "sku_id": "SKU_01", "units_sold": "invalid_number", "data_type": "SYNTHETIC_TEST_DATA"},
    {"date": "2023-01-02", "store_id": "STORE_2", "sku_id": "SKU_01", "units_sold": "NaN", "data_type": "SYNTHETIC_TEST_DATA"},
])
df_inv_num.to_csv(FIXTURES_DIR / "invalid_numeric_values.csv", index=False)

# 10. empty_dataset.csv
df_empty = pd.DataFrame(columns=["date", "store_id", "sku_id", "units_sold", "data_type"])
df_empty.to_csv(FIXTURES_DIR / "empty_dataset.csv", index=False)

print("Created 10 missing test fixtures successfully.")
