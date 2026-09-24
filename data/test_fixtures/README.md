# Controlled Test Fixtures Catalog

All files in this directory are **deterministic synthetic test fixtures** created for unit testing, integration verification, and pipeline regression testing for the **Inventory-Constrained Demand Forecasting & Allocation** platform.

> [!NOTE]
> All fixtures are clearly designated with synthetic metadata labels (`data_type="SYNTHETIC_TEST_DATA"`). No production or confidential data is contained herein.

---

## Controlled Fixtures Catalog (20 Standard Test Cases)

| # | Fixture Filename | Pipeline Target | Primary Purpose | Input Conditions | Expected Outcome | Synthetic? |
|---|---|---|---|---|---|---|
| **1** | [`normal_demand.csv`](./normal_demand.csv) | End-to-End | Normal baseline demand | 3 stores, 2 SKUs, 14 days; supply = 1,000 | Deterministic baseline forecast and complete allocation | Yes |
| **2** | [`sufficient_inventory.csv`](./sufficient_inventory.csv) | Allocation | Supply strictly exceeds demand | Demand = 50 units; inventory = 100 | Allocation = 50, shortage = 0, remaining = 50 | Yes |
| **3** | [`exact_inventory.csv`](./exact_inventory.csv) | Allocation | Supply exactly matches demand | Demand = 50 units; inventory = 50 | Allocation = 50, shortage = 0, remaining = 0 | Yes |
| **4** | [`shortage_case.csv`](./shortage_case.csv) | Allocation | Scarcity rationing (Worked Example) | A: 500, B: 400, C: 300; inventory = 1,000 | Allocations: [417, 333, 250], total shortage = 200 | Yes |
| **5** | [`zero_inventory.csv`](./zero_inventory.csv) | Allocation | Zero supply edge case | Demand > 0; available inventory = 0 | Allocations = 0; total shortage = total demand | Yes |
| **6** | [`zero_demand.csv`](./zero_demand.csv) | Forecasting / Allocation | Zero historical demand edge case | Historical units_sold = 0; supply = 500 | 0 allocation, 0 shortage, remaining = 500 | Yes |
| **7** | [`promotion_case.csv`](./promotion_case.csv) | Forecasting | Targeted store promotion adjustment | STORE_B promo multiplier = 1.30; baseline = 100 | STORE_B forecast lifts +30%; others unchanged | Yes |
| **8** | [`holiday_case.csv`](./holiday_case.csv) | Forecasting | Universal holiday demand adjustment | Holiday week toggle active; baseline = 100 | All store forecasts uplifted by +15% (1.15x) | Yes |
| **9** | [`combined_promotion_holiday_case.csv`](./combined_promotion_holiday_case.csv) | Forecasting | Interaction of promotion and holiday | Promo (1.30x) + holiday week (1.15x) | Multiplicative combination (1.495x for promoted store) | Yes |
| **10** | [`missing_dates.csv`](./missing_dates.csv) | Data Loader | Date grid completion & imputation | Incomplete store-SKU-date observations | Loader completes full Cartesian grid & imputes 0 | Yes |
| **11** | [`short_history.csv`](./short_history.csv) | Forecasting | Cold-start handling for sparse series | Stores with < 7 historical observations | Cold-start fallback calculates mean; zero NaNs | Yes |
| **12** | [`invalid_dates.csv`](./invalid_dates.csv) | Data Loader | Malformed date strings validation | 'not-a-date', '2023-99-99' | Rejection with descriptive ValueError | Yes |
| **13** | [`negative_sales.csv`](./negative_sales.csv) | Data Loader | Negative unit sales validation | units_sold < 0 | Rejection with descriptive ValueError | Yes |
| **14** | [`missing_store_id.csv`](./missing_store_id.csv) | Data Loader | Blank store ID rejection | Blank/null store_id | Rejection with descriptive ValueError | Yes |
| **15** | [`missing_sku_id.csv`](./missing_sku_id.csv) | Data Loader | Blank SKU ID rejection | Null sku_id | Rejection with descriptive ValueError | Yes |
| **16** | [`duplicate_records.csv`](./duplicate_records.csv) | Data Loader | Duplicate record detection | Multiple records on same date-store-SKU | Rejection with descriptive ValueError | Yes |
| **17** | [`invalid_numeric_values.csv`](./invalid_numeric_values.csv) | Data Loader | Non-numeric units validation | String characters in units_sold | Rejection with descriptive ValueError | Yes |
| **18** | [`rounding_case.csv`](./rounding_case.csv) | Allocation | Discrete largest-remainder tie-breaking | A: 1, B: 1, C: 1; inventory = 2 | Allocation sum exactly 2; no store > 1 | Yes |
| **19** | [`dominant_store_case.csv`](./dominant_store_case.csv) | Allocation | Extreme demand skew under severe cap | A: 1000, B: 1, C: 1; inventory = 500 | Quota allocated proportionally; total == 500 | Yes |
| **20** | [`empty_dataset.csv`](./empty_dataset.csv) | Data Loader | Zero-byte or empty table handling | 0 rows in table | Rejection with descriptive ValueError | Yes |

---

## Machine-Readable Specification

See [`fixtures_metadata.json`](./fixtures_metadata.json) for parameter bindings and expected allocation outcomes.
