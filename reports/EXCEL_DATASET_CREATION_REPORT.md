# Excel Dataset Creation Report

**Project Title:** Inventory-Constrained Demand Forecasting and Allocation  
**Execution Date:** 2026-09-24  
**Project Folder:** `D:\HTH016ML04`  
**Engineer:** Senior Retail Data Engineer, Excel Data Specialist & Dataset Validation Engineer  
**Status:** ✅ **SUCCESSFULLY GENERATED & VALIDATED**

---

## 1. Executive Overview

A complete suite of 10 enterprise-grade Excel workbooks was generated, styled, and validated using authentic retail point-of-sale and warehouse inventory source data located in `D:\HTH016ML04\data\raw\retail_store_inventory.csv`.

In strict adherence to the project's **Critical Data Authenticity Rules**:
- **Zero synthetic rows** were generated.
- **Zero row duplication** was performed.
- All 73,100 long-format records represent genuine store, SKU, and date observations.
- Complete traceability is preserved via `source_record_reference` (`RAW_SRC_ROW_<id>`) on every transactional row.
- Every workbook incorporates formal `Data_Dictionary`, `Source_Metadata`, and domain summary/validation sheets.

---

## 2. Source Dataset & Authenticity Profile

- **Source File:** `data/raw/retail_store_inventory.csv` (extracted from `data/archive (2).zip`)
- **Source Dataset Name:** Retail Store Inventory POS & Warehouse Dataset
- **Source Size:** 6,191,463 bytes (73,100 rows, 15 columns)
- **Source SHA256 Checksum:** `c7b6019887d85e6bb311a76da72560463e6bf269bfadbe4b326fbff3b1000468`
- **Authenticity Status:** `GENUINE_RETAIL_SOURCE` (`synthetic_data_used: FALSE`)
- **Date Range:** `2022-01-01` to `2024-01-01` (731 continuous calendar days)
- **Stores:** 5 (`S001`, `S002`, `S003`, `S004`, `S005`)
- **SKUs:** 20 (`P0001` through `P0020`)
- **Grid Completeness:** 5 stores × 20 SKUs × 731 dates = 73,100 records (100% full Cartesian grid).

---

## 3. Scope & Selection Parameters

### Level 1: Project Subset
- **Stores (5):** `S001`, `S002`, `S003`, `S004`, `S005`
- **SKUs (10):** `P0001`, `P0002`, `P0003`, `P0004`, `P0005`, `P0006`, `P0007`, `P0008`, `P0009`, `P0010`
- **Dates (731):** `2022-01-01` to `2024-01-01` (2 full years + 1 day)
- **Row Count:** 5 stores × 10 SKUs × 731 dates = **36,550 rows** (substantially exceeding the 18,250 1-year target).

### Level 2: Large Analytical Dataset
- **Scope:** All 5 stores × all 20 SKUs × 731 dates = **73,100 genuine rows** (100% of available eligible genuine source records, complying with authenticity constraints without row inflation).

---

## 4. Generated Excel Workbooks & Manifest

| # | Workbook File Name | Primary Sheet | Rows | Cols | File Size | SHA256 Checksum | Validation Status |
| :- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| 1 | [`01_Historical_Sales_Project_Subset.xlsx`](file:///D:/HTH016ML04/data/excel/01_Historical_Sales_Project_Subset.xlsx) | `Sales_Data` | 36,550 | 18 | 2.86 MB | `6d6b036f338fa3551b8d4a63bcf5f4f1f3e2455206b03fdbef0d5bade8427238` | PASSED |
| 2 | [`02_Calendar_Holidays.xlsx`](file:///D:/HTH016ML04/data/excel/02_Calendar_Holidays.xlsx) | `Calendar` | 731 | 17 | 73.6 KB | `4fbe237a62725ec43118cf9aa6a3c9bbcbfa7f7535fe16bc68e09f58359b36ca` | PASSED |
| 3 | [`03_Selling_Prices.xlsx`](file:///D:/HTH016ML04/data/excel/03_Selling_Prices.xlsx) | `Selling_Prices` | 10,500 | 5 | 299 KB | `ae06ef7fecfe7b4e8c148a04b500366112d7c54170889ec1b0f55cf55ce1bb49` | PASSED |
| 4 | [`04_Product_Master.xlsx`](file:///D:/HTH016ML04/data/excel/04_Product_Master.xlsx) | `Products` | 20 | 7 | 9.8 KB | `8ec063519c11cfa545b73d9dffaa2e7b95c37cb81d60b37fe878c77aa769c3a3` | PASSED |
| 5 | [`05_Store_Master.xlsx`](file:///D:/HTH016ML04/data/excel/05_Store_Master.xlsx) | `Stores` | 5 | 11 | 9.8 KB | `51637d2a2f8e00c481b85a7bfb9f8de7a76bc5856f3b0b466e582e1259f0b3ef` | PASSED |
| 6 | [`06_Inventory_Input.xlsx`](file:///D:/HTH016ML04/data/excel/06_Inventory_Input.xlsx) | `Inventory_Input` | 100 | 7 | 12.3 KB | `41c6d3663a8a3a9fbff4f3a7fe42907406da9ddc5bfae1e75e9f80164cce1e34` | PASSED |
| 7 | [`07_Promotion_Event_Data.xlsx`](file:///D:/HTH016ML04/data/excel/07_Promotion_Event_Data.xlsx) | `Event_Data` | 36,550 | 11 | 1.79 MB | `168661fc6b377f0724f8d6f9fc5c721c50d4ca6b05be174cf8f8444a72d6caee` | PASSED |
| 8 | [`08_Training_Validation_Test_Splits.xlsx`](file:///D:/HTH016ML04/data/excel/08_Training_Validation_Test_Splits.xlsx) | `Training_Data` | 36,550 | 9 | 1.72 MB | `73ca00bb2586e927806509f63541ce3855ff48bf9b7941ca6c9ce3f56ecb3474` | PASSED |
| 9 | [`09_Large_Analytical_Sales_Dataset.xlsx`](file:///D:/HTH016ML04/data/excel/09_Large_Analytical_Sales_Dataset.xlsx) | `Sales_Data` | 73,100 | 17 | 6.60 MB | `9385d91bb764406c587fb8ff4fa3d7a42c6410a05d11d994e7046e1b5af484b8` | PASSED |
| 10 | [`10_Dataset_Validation_Report.xlsx`](file:///D:/HTH016ML04/data/excel/10_Dataset_Validation_Report.xlsx) | `File_Summary` | 9 | 13 | 16.0 KB | `6da9a79fa4bb65342a77517c2f689e47feec7130b952f4eb3fafe933fa3d9646` | PASSED |

**Total Genuine Records Generated Across Workbooks:** **193,606 rows**

---

## 5. Sheet Structure Per Workbook

1. **`01_Historical_Sales_Project_Subset.xlsx`:** `Sales_Data` (36,550 rows), `Data_Dictionary` (18 rows), `Validation_Summary` (9 rows), `Source_Metadata` (18 rows).
2. **`02_Calendar_Holidays.xlsx`:** `Calendar` (731 rows), `Event_Summary` (381 rows), `Data_Dictionary` (17 rows), `Source_Metadata` (18 rows).
3. **`03_Selling_Prices.xlsx`:** `Selling_Prices` (10,500 rows), `Price_Statistics` (100 rows), `Data_Dictionary` (5 rows), `Source_Metadata` (18 rows).
4. **`04_Product_Master.xlsx`:** `Products` (20 rows), `Category_Summary` (5 rows), `Data_Dictionary` (7 rows), `Source_Metadata` (18 rows).
5. **`05_Store_Master.xlsx`:** `Stores` (5 rows), `Store_Summary` (5 rows), `Data_Dictionary` (11 rows), `Source_Metadata` (18 rows).
6. **`06_Inventory_Input.xlsx`:** `Inventory_Input` (100 rows), `Instructions` (4 rows), `Data_Dictionary` (7 rows), `Source_Metadata` (18 rows).
7. **`07_Promotion_Event_Data.xlsx`:** `Event_Data` (36,550 rows), `Promotion_Proxy` (3 rows), `Data_Dictionary` (11 rows), `Source_Metadata` (18 rows).
8. **`08_Training_Validation_Test_Splits.xlsx`:** `Training_Data` (25,600 rows), `Validation_Data` (5,500 rows), `Test_Data` (5,450 rows), `Split_Summary` (4 rows), `Data_Dictionary` (9 rows), `Source_Metadata` (18 rows).
9. **`09_Large_Analytical_Sales_Dataset.xlsx`:** `Sales_Data` (73,100 rows), `Validation_Summary` (8 rows), `Data_Dictionary` (17 rows), `Source_Metadata` (18 rows).
10. **`10_Dataset_Validation_Report.xlsx`:** 11 validation audit worksheets (`File_Summary`, `Row_Counts`, `Column_Validation`, `Missing_Values`, `Duplicate_Checks`, `Date_Coverage`, `Identifier_Coverage`, `Numeric_Validation`, `Reconciliation`, `Issues`, `Source_Traceability`).

---

## 6. Programmatic Quality & Reconciliation Verification

- **Worksheet Capacity:** All sheets strictly conform to Excel limits (max 73,100 rows vs. 1,048,576 limit). No multi-workbook splitting required.
- **Null Values:** 0 null values across all generated sales, calendar, pricing, and master data tables.
- **Uniqueness Check:** Zero duplicate composite keys across all tables.
- **Mathematical Reconciliation:**
  - `revenue == units_sold * sell_price`: 100.0% exact match across all 73,100 rows.
  - Project Subset Units Sold Sum: **4,990,323 units**.
  - Project Subset Total Revenue: **$199,444,195.44**.
  - Train (25,600 rows) + Validation (5,500 rows) + Test (5,450 rows) = **36,550 rows** (Variance: 0).
  - Train Units (3,495,150) + Val Units (755,274) + Test Units (739,899) = **4,990,323 units** (Variance: 0).
- **Time-Series Integrity:**
  - Training: `2022-01-01` to `2023-05-27` (512 dates, 70.0%)
  - Validation: `2023-05-28` to `2023-09-14` (110 dates, 15.0%)
  - Testing: `2023-09-15` to `2024-01-01` (109 dates, 15.0%)
  - Zero date overlap; 100% leak-free chronological boundary.
- **Formatting Standards:** Professional typography, bold navy headers (`#1F497D`), frozen header row panes (`A2`), enabled auto-filters, standard ISO date formatting (`YYYY-MM-DD`), right-aligned integers and currency (`$#,##0.00`).

---

## 7. Operational Rerun Commands

### Full Regeneration Command
```powershell
python scripts/create_project_excel_datasets.py --project-root . --source-dir data/raw --output-dir data/excel --store-count 5 --sku-count 10 --minimum-days 365 --large-target-rows 100000 --overwrite
```

### Validation-Only Audit Command
```powershell
python scripts/create_project_excel_datasets.py --project-root . --output-dir data/excel --validate-only
```
