# Dataset Source Missing Report

**Date of Audit:** 2026-09-24  
**Project:** Inventory-Constrained Demand Forecasting and Allocation  
**Status:** 🛑 **DATASET CREATION HALTED (Authentic Source Missing)**  

---

## 1. Reason for Stoppage

In strict accordance with **Rule #11 and #12** of the **Critical Data Authenticity Rules**:
> *"If real source files are missing, stop dataset creation and generate: `DATASET_SOURCE_MISSING.md` ... If the real source files are missing, do not silently switch to synthetic data."*

The repository was searched thoroughly, and genuine retail benchmark dataset files were not found. Generating dummy, randomly generated, or synthetic sales records to fulfill the required historical Excel workbooks (18,250+ project subset rows and 100,000+ large analytical rows) is prohibited.

---

## 2. Files & Directories Searched

### Directories Searched Recursively
- `D:\HTH016ML04\`
- `D:\HTH016ML04\backend\`
- `D:\HTH016ML04\frontend\`
- `D:\HTH016ML04\data\`
- `D:\HTH016ML04\.git\`

### Extensions Inspected
`.csv`, `.zip`, `.parquet`, `.json`, `.xls`, `.xlsx`, `.tar`, `.gz`, `.7z`

### Discovered Data Files
- `data/sales.csv` (1,492 bytes, 54 lines): Mock test fixture containing only 5 days of synthetic/sample numbers (`2023-01-01` to `2023-01-05`) for unit testing.

---

## 3. Expected Source Filenames

To build the complete suite of 10 genuine Excel workbooks, the following authentic source files are expected:

1. **`sales_train_evaluation.csv`** (or `sales_train_validation.csv`)  
   - Source for historical daily sales units by store and SKU.
2. **`calendar.csv`**  
   - Source for date mapping, day of week, SNAP flags (CA, TX, WI), cultural/religious/national event names and types.
3. **`sell_prices.csv`**  
   - Source for store-SKU weekly selling prices.

*(Optionally, any zip archive containing the official M5 Forecasting dataset: e.g., `m5-forecasting-accuracy.zip`)*.

---

## 4. Recommended Source Dataset

The recommended and preferred dataset is the **M5 Forecasting - Accuracy** retail dataset (Walmart store and SKU point-of-sale data published by the Makridakis Open Forecasting Center / Kaggle):

- **Kaggle URL:** `https://www.kaggle.com/competitions/m5-forecasting-accuracy/data`
- **Files needed:**
  - `calendar.csv` (~100 KB)
  - `sell_prices.csv` (or `sell_prices.csv.zip`)
  - `sales_train_validation.csv` (or `sales_train_evaluation.csv`)

---

## 5. Exact Location Where Source Files Must Be Placed

Place the raw files or extracted CSV files in the following path within the project:

```text
D:\HTH016ML04\data\raw\
```

Target structure:
```text
D:\HTH016ML04\
└── data/
    └── raw/
        ├── calendar.csv
        ├── sell_prices.csv
        └── sales_train_validation.csv  (or sales_train_evaluation.csv)
```

---

## 6. Exact Antigravity CLI / Project Command to Run Afterward

Once the authentic source files are placed in `data/raw/`:

### A. Run Data Preparation & Excel Generation Script
```powershell
python scripts/create_project_excel_datasets.py --project-root . --source-dir data/raw --output-dir data/excel --store-count 5 --sku-count 10 --minimum-days 365 --large-target-rows 100000 --overwrite
```

### B. Run Validation-Only Check
```powershell
python scripts/create_project_excel_datasets.py --project-root . --output-dir data/excel --validate-only
```

---

## 7. Audit Reference

For full telemetry of searched files, sizes, checksums, and schema limitations of the workspace, review:
- [SOURCE_DATA_AUDIT.md](file:///D:/HTH016ML04/reports/SOURCE_DATA_AUDIT.md)
