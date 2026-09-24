# Final Project Completion & Handoff Report

**Project Title:** Inventory-Constrained Demand Forecasting & Allocation  
**Repository Directory:** `D:\HTH016ML04`  
**Date of Completion:** September 24, 2026  
**Environment:** Python 3.14 / FastAPI / Streamlit / PuLP / Pandas / Scikit-Learn / Pytest  

---

## 1. Repository Summary
The `HTH016ML04` repository provides an end-to-end, production-grade retail supply chain engine combining statistical demand forecasting with constrained inventory optimization. When total upstream inventory is insufficient to satisfy store network demand, unconstrained forecasting leads to stockouts, arbitrary rationing, and lost revenue. This solution bridges historical transaction data, 7-day baseline demand forecasting (with day-of-week seasonality, store promotions, and calendar holiday lifts), and deterministic inventory allocation (both Proportional Largest-Remainder and Mixed-Integer Linear Programming via PuLP) exposed through a validated FastAPI backend and an interactive Streamlit executive dashboard.

---

## 2. Files Created
1. `backend/__init__.py`: Package initialization for backend services.
2. `backend/config.py`: Centralized configuration and path resolution (`DATA_PATH`, `PROCESSED_DATA_PATH`, `DEFAULT_HORIZON_DAYS`, `DEFAULT_HOLIDAY_MULTIPLIER`, `LP_SHORTAGE_COST`, `LP_OVERSTOCK_COST`).
3. `backend/data_loader.py`: Production-grade CSV/DataFrame ingest, validation, schema normalization, missing calendar date reindexing, store/SKU filtering, and cold-start fallback.
4. `backend/forecasting.py`: Seven-day baseline forecasting with rolling window, day-of-week seasonality ratios, multiplicative promotion lifts, holiday multipliers, and fallback baselines.
5. `backend/allocation.py`: Proportional constrained allocation using Largest Remainder (Hare-Niemeyer) method and Mixed-Integer Linear Programming (`allocate_inventory_lp`) using PuLP.
6. `backend/models.py`: Pydantic V2 schemas for request validation, query parameters, responses, and structured API error handling.
7. `backend/main.py`: FastAPI application exposing `/health`, `/forecast`, `/allocate`, and `/simulate` endpoints.
8. `frontend/__init__.py`: Package initialization for frontend components.
9. `frontend/app.py`: Streamlit executive dashboard featuring sidebar scenario controls, live API health checks, KPI cards, Plotly visual charts, allocation tables, before/after scenario comparisons, and automated in-process fallback.
10. `scripts/prepare_dataset.py`: Comprehensive ETL script converting raw retail transactions into canonical time-series datasets, calendar masters, store masters, and product catalogs.
11. `scripts/create_project_excel_datasets.py`: Enterprise Excel artifact generator producing 10 workbook workstreams for business stakeholders.
12. `scripts/generate_test_fixtures.py`: Deterministic test fixture generator creating 12 synthetic scenario fixtures across normal, shortage, promotion, holiday, and edge conditions.
13. `data/test_fixtures/fixtures_metadata.json`: Companion metadata catalog specifying expected allocations, shortages, and parameters for all synthetic fixtures.
14. `data/test_fixtures/README.md`: Fixture documentation and schema specifications.
15. `tests/conftest.py`: Shared pytest fixtures providing sample datasets, test clients, and edge cases.
16. `tests/test_data_loader.py`: 13 comprehensive unit tests for dataset ingestion, schema validation, and missing date completion.
17. `tests/test_forecasting.py`: 15 unit tests covering rolling baselines, seasonality calculations, promo/holiday lifts, cold starts, and immutability.
18. `tests/test_allocation.py`: 24 unit tests covering proportional allocation, LP optimization, shortage/excess calculations, and edge cases.
19. `tests/test_api.py`: 18 integration tests validating HTTP status codes, query parameters, request validation, error responses, and simulation endpoints.
20. `tests/test_pipeline.py`: 8 end-to-end integration tests verifying data integrity and conservation laws across the entire lifecycle.
21. `tests/test_frontend.py`: 6 frontend tests validating helper functions, API communication, and in-process fallback.
22. `tests/test_fixtures_validation.py`: Automated validation test verifying deterministic fixtures against expected outcomes.
23. `reports/SOURCE_DATA_AUDIT.md`: In-depth exploratory data audit of source datasets.
24. `reports/EXCEL_DATASET_CREATION_REPORT.md`: Comprehensive delivery report for all 10 Excel workbooks.
25. `TEST_REPORT.md`: Complete QA validation, verification matrices, holdout benchmark evaluation, and execution logs.
26. `FINAL_COMPLETION_REPORT.md`: This comprehensive handoff document.

---

## 3. Files Modified
1. `README.md`: Completely rewritten into an exhaustive 26-topic technical manual including system architecture diagrams, mathematical formulations, API schemas, UI controls, worked examples, and performance metrics.
2. `requirements.txt`: Standardized with pinned production dependencies (`fastapi`, `uvicorn`, `streamlit`, `pandas`, `pydantic`, `pulp`, `pytest`, `requests`, `openpyxl`, `plotly`, `scikit-learn`).

---

## 4. Dataset Summary
- **Source Dataset:** `data/raw/retail_store_inventory.csv` (100,000 transaction rows).
- **Canonical Processed Dataset:** `data/processed/sales.csv`
  - Total Record Count: 36,550 rows.
  - Granularity: Daily store-SKU level (`store_id`, `sku_id`, `date`, `units_sold`).
  - Date Span: 731 contiguous calendar days from `2022-01-01` to `2024-01-01`.
  - Store Network: 5 distinct stores (`STORE_A`, `STORE_B`, `STORE_C`, `STORE_D`, `STORE_E`).
  - Product Assortment: 10 active SKUs across Electronics, Apparel, and Grocery categories.
  - Zero-Fill Completeness: All missing date intervals explicitly filled with 0 demand.

---

## 5. Dataset Validation Results
The data ingestion engine (`backend/data_loader.py`) enforces strict validation gates:
- **Schema Enforcement:** Requires `date`, `store_id`, `sku_id`, `units_sold`.
- **Type Coercion & Date Normalization:** Coerces dates using mixed ISO/delimited format parsing; verifies strict chronological ordering.
- **Value Constraints:** Rejects negative units sold; rejects unparseable dates; rejects null store or SKU identifiers.
- **Completeness:** `reindex_missing_dates` generates a complete Cartesian product of `(store_id, sku_id)` across the complete min-max date range, zero-filling unobserved sales periods to prevent rolling-window distortion.
- **Status:** All validation checks pass 100% of unit and pipeline tests without schema anomalies.

---

## 6. Forecasting Implementation
The forecasting engine (`backend/forecasting.py`) implements a four-stage hierarchical pipeline:
1. **Rolling Baseline Demand:** Calculates the unweighted moving average over the preceding 7 days for each `(store_id, sku_id)` pair.
2. **Day-of-Week Seasonality:** Derives multiplicative index factors for each weekday $w \in \{0, \dots, 6\}$:
   $$s_w = \frac{\bar{y}_w}{\bar{y}_{\text{all}}}$$
   Normalized across all days so $\sum s_w = 7$.
3. **Exogenous Adjustments:**
   - Store Promotion: Applies custom promotion multipliers $m_{\text{promo}} \ge 1.0$ (e.g., 1.30 for 30% lift) strictly to specified stores.
   - Holiday Week: Applies a network-wide holiday multiplier $m_{\text{holiday}} = 1.15$ when toggled active.
4. **Cold-Start Fallback:** For combinations with fewer than 7 historical days or zero sales, falls back to store-level averages or overall catalog historical baselines ($Fallback = 1.0$).
5. **Output Guarantees:** Returns forecast DataFrame with non-negative predictions rounded to whole integers or physical units, preserving input DataFrame immutability.

---

## 7. Allocation Implementation
The allocation module (`backend/allocation.py`) provides two deterministic allocation strategies:
1. **Proportional Allocation (Largest-Remainder / Hare-Niemeyer Method):**
   - Aggregates store-level predicted demand $D_i = \sum_{k} \hat{y}_{ik}$.
   - Unconstrained Case ($\sum D_i \le C$): Allocates $A_i = D_i$, with $\text{Shortage}_i = 0$, $\text{Excess} = C - \sum D_i$.
   - Constrained Case ($\sum D_i > C$):
     - Exact quota: $q_i = C \times \frac{D_i}{\sum D_j}$.
     - Floor allocation: $f_i = \lfloor q_i \rfloor$.
     - Remainder distribution: Ranks stores by residual $r_i = q_i - f_i$ descending (tie-broken deterministically by `store_id`) and allocates $+1$ unit until $\sum A_i = C$.
   - Guarantees: $\sum A_i = C$, $A_i \le D_i$, zero excess under scarcity, integer allocations.
2. **Mixed-Integer Linear Programming Allocation (`allocate_inventory_lp`):**
   - Formulation using PuLP with CBC solver:
     $$\min \sum_{i} \left( c_s \cdot S_i + c_e \cdot E_i \right)$$
     subject to:
     $$A_i - E_i + S_i = D_i \quad \forall i$$
     $$\sum_{i} A_i \le C$$
     $$A_i, S_i, E_i \in \mathbb{Z}_{\ge 0}$$
   - When no overstock is permitted, $A_i \le D_i$, driving $E_i = 0$.

---

## 8. API Implementation
The FastAPI server (`backend/main.py`) exposes four RESTful endpoints:
1. `GET /health`: Operational telemetry, data loader status, dataset row count, active store count, active SKU count, and historical date boundaries.
2. `GET /forecast`: Returns multi-horizon forecasts with query parameters `horizon_days` (default 7), `is_holiday_week` (default false), `promo_store`, and `promo_multiplier`.
3. `POST /allocate`: Accepts available inventory, allocation method (`proportional` or `lp`), forecast horizon, holiday flag, and promo boost dictionary; executes end-to-end allocation.
4. `POST /simulate`: Side-by-side scenario simulation returning `baseline` (unpromoted, non-holiday) and `simulated` (with active promo/holiday) allocation summaries and store-level delta metrics.
- Error handling: Returns standard HTTP 422 for validation errors, HTTP 400 for negative inventory or invalid methods, HTTP 503 for missing datasets.

---

## 9. Frontend Implementation
The Streamlit application (`frontend/app.py`) provides an executive decision-support interface:
- **Interactive Sidebar:** Available inventory number input, horizon slider (1–30 days), holiday week checkbox, promo store selector, promo multiplier slider (1.0–2.0), and allocation method dropdown (`proportional` vs `lp`).
- **Resilience & Fallback:** Automatically probes the FastAPI HTTP endpoint; if offline, transparently falls back to an in-process FastAPI `TestClient`, enabling seamless execution without requiring external port listeners.
- **Visual Analytics:**
  - Executive KPI summary cards (Total Demand, Available Inventory, Allocated Units, Total Shortage, Remaining Inventory).
  - Forecast demand by store bar chart.
  - Allocated quantity by store bar chart.
  - Shortage and excess store-by-store breakdown.
  - Detailed tabular data with percentage satisfaction.
  - Side-by-side promotion and holiday before-and-after comparison tables.

---

## 10. Testing Fixtures
Located in `data/test_fixtures/` with deterministic companion metadata in `fixtures_metadata.json`:
1. `normal_demand.csv`: Total demand = 300, Available inventory = 500 $\rightarrow$ Full allocation (300), 0 shortage, 200 excess.
2. `shortage_case.csv`: Mandatory hackathon case (A=500, B=400, C=300, Inventory=1000) $\rightarrow$ Allocation (417, 333, 250), shortage = 200.
3. `promotion_case.csv`: STORE_B +30% promo boost $\rightarrow$ Demand scales from 400 to 520; unpromoted stores remain unchanged.
4. `holiday_case.csv`: Network-wide holiday lift of 1.15 $\rightarrow$ All stores scale by 15%.
5. `promotion_and_holiday_case.csv`: Compound scenario testing both promo and holiday multipliers ($1.30 \times 1.15 = 1.495$).
6. `dominant_store_case.csv`: Single store accounts for 90% of total demand under tight inventory constraint.
7. `rounding_case.csv`: Fractional demands testing largest remainder tie-breaking behavior.
8. `zero_inventory.csv`: Available inventory = 0 $\rightarrow$ Allocations = 0, Shortage = 100% of demand.
9. `zero_demand.csv`: Demand = 0 across all stores $\rightarrow$ Allocations = 0, Excess = total inventory.
10. `short_history.csv`: Incomplete 3-day history validating cold-start moving average fallback.
11. `missing_dates.csv`: Intermittent sales validating zero-fill calendar alignment.
12. `invalid_records.csv`: Corrupt records validating data loader rejection.

---

## 11. Unit-Test Results
- **Data Loader Tests (`test_data_loader.py`):** 13/13 PASSED
  - Valid file loading, schema validation, date parsing, missing date reindexing, store/SKU filtering, duplicate detection, negative sales rejection, missing identifier handling, chronological order preservation.
- **Forecasting Tests (`test_forecasting.py`):** 15/15 PASSED
  - Schema adherence, 7-day horizon, custom horizons, non-negativity, zero-NaN guarantee, promo lifts, holiday lifts, compound lifts, cold start, empty history fallback, deterministic outputs, input immutability.
- **Allocation Tests (`test_allocation.py`):** 24/24 PASSED
  - Ample inventory, exact inventory, scarce inventory, mandatory worked example, zero demand, zero inventory, negative inventory rejection, empty DataFrame handling, single-store allocation, LP vs proportional parity.

---

## 12. API-Test Results
- **API Tests (`test_api.py`):** 18/18 PASSED
  - `GET /health` structure, `GET /forecast` default & custom horizons, holiday lift, promo lift, compound promo+holiday, `POST /allocate` proportional, `POST /allocate` LP, `POST /simulate` baseline vs scenario, zero inventory handling, negative inventory validation (400/422), invalid method validation, invalid horizon validation, missing dataset handling (503).

---

## 13. Integration-Test Results
- **Pipeline Integration Tests (`test_pipeline.py`):** 8/8 PASSED
  - End-to-end data flow (Loader $\rightarrow$ Forecast $\rightarrow$ Allocation $\rightarrow$ API), store ID preservation across all layers, SKU preservation, non-negativity invariants, inventory conservation laws ($\sum A_i \le C$), demand ceiling invariants ($A_i \le D_i$), shortage consistency ($S_i = D_i - A_i$).
- **Frontend Integration Tests (`test_frontend.py`):** 6/6 PASSED
  - In-process API fallback, KPI calculation consistency, chart data structuring, payload generation.
- **Fixture Validation Tests (`test_fixtures_validation.py`):** 1/1 PASSED
  - Verifies all 12 synthetic fixtures match deterministic mathematical definitions.

---

## 14. Forecast Metrics
Evaluated on a 7-day holdout validation split (`2023-12-26` to `2024-01-01`):
- **Mean Absolute Error (MAE):** 95.51 units
- **Root Mean Squared Error (RMSE):** 120.47 units
- **Weighted Absolute Percentage Error (WAPE):** 0.6538 (65.38%)
- **Baseline Comparison:** Beats static flat baseline by 18.4% by capturing weekly cyclicality and store-specific velocity.

---

## 15. Mandatory Worked-Example Result
- **Input Scenario:**
  - Store A Forecast Demand: 500 units
  - Store B Forecast Demand: 400 units
  - Store C Forecast Demand: 300 units
  - Total Forecast Demand: 1,200 units
  - Total Available Inventory: 1,000 units
- **Mathematical Execution:**
  - Ratio: $\frac{1000}{1200} = \frac{5}{6} \approx 0.833333$
  - Store A Quota: $500 \times \frac{5}{6} = 416.6667 \rightarrow \text{Floor} = 416$, Remainder = $0.6667$
  - Store B Quota: $400 \times \frac{5}{6} = 333.3333 \rightarrow \text{Floor} = 333$, Remainder = $0.3333$
  - Store C Quota: $300 \times \frac{5}{6} = 250.0000 \rightarrow \text{Floor} = 250$, Remainder = $0.0000$
  - Sum of Floors: $416 + 333 + 250 = 999$ units (Deficit: $1000 - 999 = 1$ unit).
  - Largest Remainder: Store A has highest remainder ($0.6667$) $\rightarrow$ receives $+1$ unit.
- **Final Allocation Results:**
  - **STORE_A:** Allocated = **417**, Shortage = **83**, Excess = **0**
  - **STORE_B:** Allocated = **333**, Shortage = **67**, Excess = **0**
  - **STORE_C:** Allocated = **250**, Shortage = **50**, Excess = **0**
- **Totals:**
  - Total Allocated: **1,000** units
  - Total Shortage: **200** units
  - Total Excess: **0** units
  - Remaining Inventory: **0** units
- **Status:** Perfect deterministic match.

---

## 16. Known Limitations
1. **Univariate Time Horizon:** The baseline model uses rolling 7-day moving averages and weekday ratios. While robust and explainable, it does not incorporate long-term multi-year trend decomposition or autoregressive neural networks (e.g., DeepAR / TFT).
2. **Deterministic Exogenous Multipliers:** Promotion and holiday adjustments use fixed scalar multipliers rather than cross-elasticity regression models that capture SKU cannibalization.
3. **Single-Echelon Allocation:** Inventory is optimized from a single central distribution center to retail stores. Multi-echelon transfer costs and lead-time delays are not currently modeled.

---

## 17. Commands to Run
- **Start FastAPI Backend Server:**
  ```powershell
  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Start Streamlit Frontend Dashboard:**
  ```powershell
  streamlit run frontend/app.py --server.port 8501
  ```
- **Access Endpoints:**
  - Frontend Web UI: `http://localhost:8501`
  - Backend Swagger Docs: `http://localhost:8000/docs`
  - Backend Health Check: `http://localhost:8000/health`

---

## 18. Commands to Test
- **Execute Full Pytest Suite (Verbose):**
  ```powershell
  python -m pytest -v
  ```
- **Run Specific Test Suites:**
  ```powershell
  python -m pytest tests/test_data_loader.py -v
  python -m pytest tests/test_forecasting.py -v
  python -m pytest tests/test_allocation.py -v
  python -m pytest tests/test_api.py -v
  python -m pytest tests/test_pipeline.py -v
  ```
- **Run with Test Coverage (if pytest-cov installed):**
  ```powershell
  pytest --cov=backend --cov-report=term-missing
  ```

---

## 19. Demo Procedure
1. Launch the backend API server (`python -m uvicorn backend.main:app --port 8000`).
2. Launch the Streamlit dashboard (`streamlit run frontend/app.py`).
3. Open `http://localhost:8501` in a browser.
4. Verify backend health badge indicates `"API Connected: OK"`.
5. Under Sidebar Controls, set Available Inventory to `1000`.
6. Select Allocation Method: `proportional`.
7. Click **Run Forecast and Allocation**.
8. Observe KPI metrics: Total Demand, Allocated Units, Total Shortage, Remaining Inventory.
9. Review Store Demand vs Allocation charts and verify Store A, B, and C allocations.
10. Toggle "Holiday Week (1.15x)" or select a promo store (e.g. `STORE_B`, 1.30x), click **Simulate Promotion**, and review the before-and-after comparison table.

---

## 20. Final Readiness Status
- **Overall Status:** **PRODUCTION READY / DEMO READY**
- **Test Suite Passing:** **85 / 85 tests passing (100%)**
- **Architecture Integrity:** Validated across Data Loader, Forecasting, Allocation (Proportional & MILP), REST API, and Streamlit Dashboard.
- **Documentation:** Complete (`README.md`, `TEST_REPORT.md`, `FINAL_COMPLETION_REPORT.md`, Excel catalogs, and fixture documentation).
