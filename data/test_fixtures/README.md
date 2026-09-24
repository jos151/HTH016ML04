# Test Fixtures Manifest

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
