# Manual Web Interface & User Journey Test Report

**Project Title:** Inventory-Constrained Demand Forecasting & Allocation Platform  
**Test Date:** 2026-09-25  
**Execution Environment:** Windows, Python 3.14.2, Streamlit 1.50+, FastAPI 0.115+, Uvicorn  
**Tested URLs:**  
- Web Frontend: `http://127.0.0.1:8501`  
- REST Backend: `http://127.0.0.1:8000`  

---

## User Journey Test Results

### User Journey 1: Baseline Forecast
- **Step:** Open dashboard, navigate to "📈 Demand Forecasting", select 7-day horizon, baseline forecast.
- **Expected Result:** Status badge shows "Backend Online", 350 forecast rows generated (5 stores × 10 SKUs × 7 days), non-negative demand, interactive charts load.
- **Actual Result:** `GET /forecast?horizon_days=7` returned HTTP 200, 350 rows. Line chart rendered without error.
- **Status:** **PASS**

---

### User Journey 2: Constrained Inventory Allocation (Mandatory Demo Case)
- **Step:** Navigate to "⚖️ Inventory Allocation", input 1,000 available units, select "proportional" largest-remainder method.
- **Expected Result:** Total allocated units = 1,000. Shortage = Total Demand - 1,000. Remaining inventory = 0. Individual store allocations sum to exactly 1,000.
- **Actual Result:** `POST /allocate` returned HTTP 200. Total allocated = 1,000.0, shortage calculated consistently, all units integer-valued.
- **Status:** **PASS**

---

### User Journey 3: Promotional Scenario
- **Step:** Navigate to "🧪 Scenario Simulator", select `STORE_1`, input 1.30 promo multiplier (+30% boost).
- **Expected Result:** Demand for `STORE_1` increases by +30%; unselected stores (`STORE_2` through `STORE_5`) remain identical to baseline. Overall demand lift ~ +5.31%. Allocation recalculated.
- **Actual Result:** `POST /simulate` returned HTTP 200. Lift percentage: +5.31%. Reallocation dynamically shifted units toward `STORE_1`.
- **Status:** **PASS**

---

### User Journey 4: Holiday Week Uplift
- **Step:** Navigate to "🧪 Scenario Simulator", toggle "Holiday Week (+15% Uplift)".
- **Expected Result:** Demand scales by 1.15x (+15%) across all stores. Shortage increases under fixed 1,000 inventory.
- **Actual Result:** `POST /simulate` returned HTTP 200. Lift percentage: exactly +15.0%.
- **Status:** **PASS**

---

### User Journey 5: Zero Inventory Edge Case
- **Step:** Enter `0` in Available Inventory units in Allocation section.
- **Expected Result:** Allocation across all stores equals 0; total shortage equals total demand (51,129 units); high-severity warning banner is displayed.
- **Actual Result:** `POST /allocate` returned HTTP 200. `total_allocated_units: 0.0`, `total_shortage: 51129.0`. Warning rendered clearly.
- **Status:** **PASS**

---

### User Journey 6: Abundant / Sufficient Inventory
- **Step:** Enter `100,000` units in Available Inventory (exceeding total 7-day demand of 51,129 units).
- **Expected Result:** 100% fulfillment across all stores. Shortage = 0. Remaining inventory = 48,871 units.
- **Actual Result:** `POST /allocate` returned HTTP 200. `total_allocated_units: 51129.0`, `total_shortage: 0.0`, `remaining_inventory: 48871.0`.
- **Status:** **PASS**

---

### User Journey 7: Defensive Negative Input Handling
- **Step:** Enter `-50` in Available Inventory units.
- **Expected Result:** Request rejected with HTTP 422 Unprocessable Entity and clear actionable error message. Application does not crash.
- **Actual Result:** API returned HTTP 422: `Value error, total_available_units must be non-negative (>= 0)`. Frontend caught error and presented error callout without traceback.
- **Status:** **PASS**

---

### User Journey 8: Download Analytical Report
- **Step:** Navigate to "📑 Reports & Exports", click "Download Full Analytical Report (.xlsx)".
- **Expected Result:** 8-worksheet Excel workbook (`inventory_allocation_report.xlsx`) generated and downloaded with valid OpenXML MIME type.
- **Actual Result:** `POST /reports/export` returned HTTP 200, 20,721 bytes, MIME `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. All 8 sheets present and formatted.
- **Status:** **PASS**

---

## Journey Execution Summary Matrix

| Journey # | Title | Target Endpoint / UI Component | HTTP Code | Status | Notes |
|:---|:---|:---|:---|:---|:---|
| **J1** | Baseline Forecast | `GET /forecast` | 200 OK | **PASS** | 350 predictions generated deterministically |
| **J2** | Inventory Allocation | `POST /allocate` | 200 OK | **PASS** | 1,000 units rationed by largest remainder |
| **J3** | Promotion Boost | `POST /simulate` | 200 OK | **PASS** | Store-isolated +30% uplift verified |
| **J4** | Holiday Uplift | `POST /simulate` | 200 OK | **PASS** | System-wide +15% uplift verified |
| **J5** | Zero Inventory | `POST /allocate` | 200 OK | **PASS** | 0 allocation, shortage = 51,129 |
| **J6** | Sufficient Supply | `POST /allocate` | 200 OK | **PASS** | 0 shortage, remaining = 48,871 |
| **J7** | Negative Input | `POST /allocate` | 422 Unproc | **PASS** | Rejected safely with clear message |
| **J8** | Report Export | `POST /reports/export` | 200 OK | **PASS** | 20,721 bytes 8-tab workbook |

**Overall Manual UI Validation Status:** **READY FOR DEMO**
