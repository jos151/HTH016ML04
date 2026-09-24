# QA Defect Management Log

**Project Title:** Inventory-Constrained Demand Forecasting & Allocation Platform  
**Test Cycle:** Final QA & Validation Sprint  
**Date:** 2026-09-25  

---

## Defect Summary Matrix

| Defect ID | Severity | Priority | Component | File | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-001** | High | High | Networking / Proxy | `frontend/app.py`, `tests/conftest.py` | **CLOSED (Verified)** |
| **DEF-002** | Medium | Medium | Frontend Client | `frontend/app.py` | **CLOSED (Verified)** |
| **DEF-003** | Low | Medium | Data Ingestion | `backend/data_loader.py` | **CLOSED (Verified)** |
| **DEF-004** | Medium | Medium | Data Loader | `backend/data_loader.py` | **CLOSED (Verified)** |
| **DEF-005** | Medium | High | Forecast Metrics | `backend/forecasting.py` | **CLOSED (Verified)** |
| **DEF-006** | Low | Low | Optimizer Tests | `tests/test_optimizer.py` | **CLOSED (Verified)** |

---

## Detailed Defect Records

### DEF-001: Localhost Proxy Interception of Local REST Calls
- **Severity:** High | **Priority:** High
- **Component:** Network Integration
- **File:** [`frontend/app.py`](file:///D:/HTH016ML04/frontend/app.py), [`tests/conftest.py`](file:///D:/HTH016ML04/tests/conftest.py)
- **Test That Exposed It:** `tests/test_frontend.py::test_frontend_call_allocate_baseline`
- **Input Used:** HTTP requests to `http://127.0.0.1:8000/allocate`
- **Expected Result:** Direct TCP socket connection to local FastAPI Uvicorn process.
- **Actual Result:** `HTTP 400 Direct IP access is not allowed` returned by external system proxy.
- **Root Cause:** Environment variable `HTTP_PROXY` was configured by the sandbox/corporate proxy, but `NO_PROXY` was not set, causing requests library to route `127.0.0.1` outbound.
- **Fix Applied:** Configured `os.environ["NO_PROXY"] = "localhost,127.0.0.1"` at module load in `frontend/app.py` and `tests/conftest.py`.
- **Retest Result:** **PASSED** (Direct local communication verified with HTTP 200).
- **Regression Result:** All 6 frontend tests pass.
- **Remaining Risk:** None.

---

### DEF-002: Error Payload Serialization in Frontend API Helper
- **Severity:** Medium | **Priority:** Medium
- **Component:** Frontend Error Handling
- **File:** [`frontend/app.py`](file:///D:/HTH016ML04/frontend/app.py)
- **Test That Exposed It:** `tests/test_frontend.py::test_frontend_call_allocate_invalid_method`
- **Input Used:** `method="heuristic_unknown"`
- **Expected Result:** Actionable error string returned to caller for UI presentation.
- **Actual Result:** Returned raw list of dicts `[{"loc": ["body", "method"], ...}]`.
- **Root Cause:** FastAPI 422 details are structured lists; frontend was returning `resp.json().get("detail")` directly.
- **Fix Applied:** Implemented `_format_error(resp)` converting structured detail payloads into clean, stringified JSON or text.
- **Retest Result:** **PASSED**.
- **Regression Result:** Substring checks and UI alerts render cleanly.
- **Remaining Risk:** None.

---

### DEF-003: Missing In-Memory DataFrame Validation Helper
- **Severity:** Low | **Priority:** Medium
- **Component:** Data Loader
- **File:** [`backend/data_loader.py`](file:///D:/HTH016ML04/backend/data_loader.py)
- **Test That Exposed It:** `tests/test_data_validation.py`
- **Input Used:** In-memory pandas DataFrame
- **Expected Result:** Validation without saving to disk or mutating the original DataFrame.
- **Actual Result:** Only file-based `load_demand_data` was publicly exposed.
- **Root Cause:** Validation functions were private (`_validate_columns`, etc.).
- **Fix Applied:** Implemented and exported `validate_sales_df(df: pd.DataFrame) -> pd.DataFrame` performing deep-copy validation.
- **Retest Result:** **PASSED**.
- **Regression Result:** All 22 loader and validation tests pass.
- **Remaining Risk:** None.

---

### DEF-004: Missing File Extension Filter in Data Loader
- **Severity:** Medium | **Priority:** Medium
- **Component:** Data Loader
- **File:** [`backend/data_loader.py`](file:///D:/HTH016ML04/backend/data_loader.py)
- **Test That Exposed It:** `tests/test_data_validation.py::test_unsupported_file_extension`
- **Input Used:** Loading `sales.txt`
- **Expected Result:** Reject unsupported file extensions with descriptive ValueError.
- **Actual Result:** Unconditionally attempted `pd.read_csv`.
- **Root Cause:** Suffix inspection was not implemented prior to parsing.
- **Fix Applied:** Added suffix check requiring `.csv`, `.xlsx`, or `.xls`, routing Excel files to `pd.read_excel`.
- **Retest Result:** **PASSED**.
- **Regression Result:** Unchanged CSV handling; unsupported types rejected cleanly.
- **Remaining Risk:** None.

---

### DEF-005: Forecast Accuracy Metric Invariants and Bias Calculation
- **Severity:** Medium | **Priority:** High
- **Component:** Forecasting Analytics
- **File:** [`backend/forecasting.py`](file:///D:/HTH016ML04/backend/forecasting.py)
- **Test That Exposed It:** `tests/test_forecast_metrics.py`
- **Input Used:** Evaluation arrays with NaN or negative values.
- **Expected Result:** Rejection of invalid inputs and calculation of forecast bias ($\text{Bias} = \text{mean}(y_{\text{pred}} - y_{\text{true}})$).
- **Actual Result:** Returned only MAE, RMSE, WAPE; did not validate NaN or negative demand.
- **Root Cause:** `calculate_forecast_metrics` lacked explicit defense checks for corrupted inputs.
- **Fix Applied:** Added checks for `np.isnan` and negative actuals; added `bias` to output dictionary.
- **Retest Result:** **PASSED**.
- **Regression Result:** All 23 forecasting tests pass.
- **Remaining Risk:** None.

---

### DEF-006: Strict Identity Comparison on PuLP Solver Availability
- **Severity:** Low | **Priority:** Low
- **Component:** Unit Tests
- **File:** [`tests/test_optimizer.py`](file:///D:/HTH016ML04/tests/test_optimizer.py)
- **Test That Exposed It:** `tests/test_optimizer.py::test_lp_solver_availability`
- **Input Used:** `solver.available()`
- **Expected Result:** Solver is truthy and executable path is verified.
- **Actual Result:** Assertion failed because `solver.available()` returns the path string `.../cbc.exe` rather than boolean `True`.
- **Root Cause:** PuLP returns the binary path on availability; test asserted `is True`.
- **Fix Applied:** Changed assertion to `bool(solver.available()) is True`.
- **Retest Result:** **PASSED**.
- **Regression Result:** All optimizer tests pass.
- **Remaining Risk:** None.
