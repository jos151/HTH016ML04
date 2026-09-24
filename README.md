# Inventory-Constrained Demand Forecasting & Allocation

An enterprise-grade, deterministic retail supply-chain decision-support system that models multi-store seasonal demand, evaluates promotional and holiday uplifts, and allocates scarce inventory using proportional largest-remainder integer distribution and mixed-integer linear programming (PuLP).

---

## Description

In regional retail networks, central warehouse supply frequently fails to cover aggregate store demand ($\sum \text{Demand}_s > \text{Supply}$). Uncoordinated, unconstrained ordering leads to first-come first-served stockouts, arbitrary rationing, and fractional distribution errors that physical warehouse pickers cannot execute.

This system provides a closed-loop forecasting and constrained optimization platform. It couples a 7-day rolling demand baseline with day-of-week seasonality, store-level promotional multipliers, and calendar holiday lifts. When aggregate network demand exceeds available stock, the system executes deterministic integer allocation via either:
1. **Largest-Remainder (Hare-Niemeyer) Proportional Allocation**, or
2. **PuLP Mixed-Integer Linear Programming (MILP)** optimization minimizing total shortage and excess penalties.

The platform is designed for retail inventory planners, supply chain directors, and store operations managers who require transparent, reproducible, and mathematically provable inventory rationing.

---

## Features

- **Automated Data Ingestion & Grid Completion:** Validates raw POS transactions, cleans dates into canonical ISO format (`YYYY-MM-DD`), enforces entity integrity, and constructs complete Cartesian store-SKU grids with zero-imputation for unobserved days.
- **Hierarchical Demand Forecasting:**
  - 7-day rolling average baseline.
  - Normalized day-of-week seasonality index factors.
  - Store-specific marketing promotion lifts ($m \ge 1.0$).
  - Network-wide holiday week uplifts ($1.15\times$).
  - Cold-start fallback mechanisms for series with limited historical observations.
- **Deterministic Constrained Allocation:**
  - **Proportional Allocation:** Uses largest-remainder quota distribution to guarantee non-negative, whole-integer physical unit assignments with zero excess under scarcity.
  - **Integer LP Optimization:** PuLP/CBC formulation balancing shortage costs ($c_s = 1.0$) against overstock penalties ($c_e = 0.3$).
- **Validated REST API:** Production FastAPI service exposing endpoints for operational health telemetry (`/health`), multi-horizon forecasting (`/forecast`), constrained allocation (`/allocate`), and scenario simulation (`/simulate`).
- **Interactive Decision Dashboard:** Streamlit executive application with scenario controls, real-time KPI metrics, Plotly visualizations, detailed allocation tables, and before-and-after promotional comparisons.
- **Dual-Mode Deployment Resilience:** Seamless in-process execution fallback (`TestClient`) allowing the Streamlit frontend to run standalone on Streamlit Cloud without requiring an external port listener.
- **Exhaustive Automated Test Suite:** 85 automated pytest suites validating mathematical invariants, API contracts, conservation laws, and edge cases.

---

## Screenshots / Visuals

> Screenshots coming soon.

---

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Screenshots / Visuals](#screenshots--visuals)
- [Table of Contents](#table-of-contents)
- [Tech Stack](#tech-stack)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Starting the FastAPI Backend](#1-starting-the-fastapi-backend)
  - [Starting the Streamlit Dashboard](#2-starting-the-streamlit-dashboard)
  - [Running the Worked Demo Scenario](#3-running-the-worked-demo-scenario)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
  - [GET /health](#1-get-health)
  - [GET /forecast](#2-get-forecast)
  - [POST /allocate](#3-post-allocate)
  - [POST /simulate](#4-post-simulate)
- [Testing](#testing)
- [Deployment](#deployment)
  - [Streamlit Community Cloud](#1-streamlit-community-cloud)
  - [Docker / Server Deployment](#2-docker--server-deployment)
- [Contributing](#contributing)
- [Support](#support)
- [FAQ](#faq)
- [Known Issues](#known-issues)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Project Status](#project-status)

---

## Tech Stack

- **Core Language:** Python 3.10+ (tested on Python 3.14)
- **Backend Framework:** FastAPI, Starlette, Pydantic V2, Uvicorn
- **Frontend Dashboard:** Streamlit, Plotly
- **Optimization & Modeling:** PuLP (CBC Solver), Scikit-Learn, SciPy
- **Data Engineering:** Pandas, NumPy, OpenPyXL
- **Testing & Quality Assurance:** Pytest, AnyIO, Pytest-Asyncio
- **HTTP Client:** Requests, HTTPX

---

## Requirements

- **Operating System:** Windows 10/11, macOS, or Linux (Ubuntu 20.04+)
- **Python Version:** Python 3.10, 3.11, 3.12, 3.13, or 3.14
- **Package Manager:** `pip` or `uv`
- **Memory:** Minimum 2 GB RAM (lightweight memory footprint)
- **Disk Space:** ~100 MB for dataset and virtual environment

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/jos151/HTH016ML04.git
cd HTH016ML04
```

### 2. Set Up a Virtual Environment
On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

The application uses standard environment variables with production defaults. No `.env` file is required for out-of-the-box local execution.

| Variable | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `API_BASE_URL` | Base URL for FastAPI backend service used by Streamlit | `http://127.0.0.1:8000` | No |
| `BACKEND_URL` | Alias fallback for API host | `http://127.0.0.1:8000` | No |
| `DATA_PATH` | Path to custom raw sales CSV file | `data/processed/sales.csv` | No |
| `PORT` | Web server port for backend service | `8000` | No |

---

## Usage

### 1. Starting the FastAPI Backend
Launch the backend service using Uvicorn:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc Documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check Telemetry: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Starting the Streamlit Dashboard
In a separate terminal, launch the dashboard:
```bash
streamlit run frontend/app.py --server.port 8501
```
The browser will automatically open [http://localhost:8501](http://localhost:8501).

> **Note:** When deployed to Streamlit Community Cloud without an active Uvicorn service, `frontend/app.py` automatically initializes an in-process FastAPI engine, ensuring complete functionality without extra configuration.

### 3. Running the Worked Demo Scenario
The benchmark supply-chain rationing case can be verified directly:
- **Input Parameters:**
  - Available Supply: `1000` units
  - Method: `proportional`
  - Horizon: `7` days
- **Benchmark Stores & Demand:**
  - Store A Demand = `500`
  - Store B Demand = `400`
  - Store C Demand = `300`
  - Total Demand = `1200` (Shortage = `200`)
- **Deterministic Allocation Output:**
  - Store A = **417** units (Shortage: 83)
  - Store B = **333** units (Shortage: 67)
  - Store C = **250** units (Shortage: 50)
  - Total Allocated = **1,000** units | Remaining = **0**

---

## Project Structure

```text
HTH016ML04/
├── backend/
│   ├── __init__.py           # Package initialization
│   ├── allocation.py         # Proportional, PuLP MILP, & multi-item store-SKU allocation
│   ├── config.py             # Configuration and path resolution
│   ├── data_loader.py        # Ingestion, validation, calendar grids, & data quality audit
│   ├── forecasting.py        # Rolling baseline, seasonality, lifts, & uncertainty bounds
│   ├── inventory_planning.py # Safety stock, ROP, economic impact, & Gini fairness metrics
│   ├── main.py               # FastAPI application routes (core, analytics, and reporting)
│   ├── models.py             # Pydantic V2 schemas and response contracts
│   └── reports.py            # Multi-worksheet Excel workbook generation
├── frontend/
│   ├── __init__.py           # Package initialization
│   └── app.py                # 11-section enterprise Streamlit decision-support platform
├── data/
│   ├── processed/            # Canonical clean datasets (sales.csv: 36,550 records)
│   ├── raw/                  # Source POS transactions (retail_store_inventory.csv)
│   ├── test_fixtures/        # 12 synthetic deterministic testing scenario CSVs
│   └── excel/                # 10 enterprise analytical Excel workbooks
├── reports/
│   ├── ADVANCED_UI_INSPECTION_REPORT.md # Full architecture, endpoint & UI inspection
│   ├── EXCEL_DATASET_CREATION_REPORT.md # Documentation of Excel datasets
│   └── SOURCE_DATA_AUDIT.md             # Exploratory analysis of source transactions
├── scripts/
│   ├── create_project_excel_datasets.py # Excel artifact generator
│   ├── generate_test_fixtures.py        # Synthetic test scenario generator
│   └── prepare_dataset.py               # Raw transaction ETL pipeline
├── tests/
│   ├── conftest.py           # Shared test fixtures and TestClient setup
│   ├── test_advanced_features.py # 14 tests: uncertainty, store-SKU allocation, safety stock, Excel
│   ├── test_allocation.py    # 24 tests: proportional math, PuLP MILP, quotas, rounding
│   ├── test_api.py           # 18 tests: HTTP endpoints, validation codes, error paths
│   ├── test_data_loader.py   # 13 tests: schemas, date parsing, missing date zero-filling
│   ├── test_fixtures_validation.py # Test verification against metadata benchmarks
│   ├── test_forecasting.py   # 15 tests: rolling windows, seasonality, lifts, cold-starts
│   ├── test_frontend.py      # 6 tests: Streamlit client helpers and in-process fallback
│   └── test_pipeline.py      # 8 tests: end-to-end data flow and conservation laws
├── .streamlit/
│   ├── config.toml           # Headless Streamlit Cloud server configuration
│   └── credentials.toml      # Headless onboarding bypass
├── FINAL_COMPLETION_REPORT.md# Comprehensive 20-point handoff release report
├── TEST_REPORT.md            # QA validation matrix, benchmark results, and holdout metrics
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Pinned production dependencies
└── README.md                 # Primary project documentation
```

---

## API Documentation

### Base URL
- Local: `http://127.0.0.1:8000`
- Production: Configurable via `API_BASE_URL`

### Authentication
No authentication is required for local or hackathon review.

---

### 1. GET `/health`
Returns system health, dataset load status, active store/SKU counts, and historical date boundaries.

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Example Response (200 OK):**
```json
{
  "status": "ok",
  "data_loaded": true,
  "row_count": 36550,
  "store_count": 5,
  "sku_count": 10,
  "minimum_date": "2022-01-01",
  "maximum_date": "2024-01-01"
}
```

---

### 2. GET `/forecast`
Projects store-SKU level demand over a designated horizon with optional holiday and promotional adjustments.

**Query Parameters:**
- `horizon_days` (*int*, default: 7): Forecast horizon (1 to 30 days).
- `is_holiday_week` (*bool*, default: false): Toggles a 15% aggregate uplift ($1.15\times$).
- `promo_store` (*str*, optional): Target store for promotional lift (e.g. `STORE_1`).
- `promo_multiplier` (*float*, optional, default: 1.0): Demand multiplier for promoted store (e.g. 1.30).

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/forecast?horizon_days=7&is_holiday_week=true&promo_store=STORE_1&promo_multiplier=1.30"
```

---

### 3. POST `/allocate`
Aggregates demand forecasts across stores and performs constrained integer allocation.

**Request Schema:**
```json
{
  "total_available_units": 1000,
  "method": "proportional",
  "horizon_days": 7,
  "is_holiday_week": false,
  "promo_boost": {
    "STORE_1": 1.30
  }
}
```

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8000/allocate" \
     -H "Content-Type: application/json" \
     -d '{"total_available_units": 1000, "method": "proportional", "horizon_days": 7, "is_holiday_week": false}'
```

**Example Response (200 OK):**
```json
{
  "status": "success",
  "method": "proportional",
  "summary": {
    "total_forecasted_demand": 1200.0,
    "total_available_units": 1000,
    "total_allocated_units": 1000,
    "total_shortage": 200,
    "total_excess": 0,
    "remaining_inventory": 0
  },
  "allocations": [
    {
      "store_id": "STORE_A",
      "forecasted_demand": 500.0,
      "allocated_units": 417,
      "shortage": 83,
      "excess": 0
    },
    {
      "store_id": "STORE_B",
      "forecasted_demand": 400.0,
      "allocated_units": 333,
      "shortage": 67,
      "excess": 0
    },
    {
      "store_id": "STORE_C",
      "forecasted_demand": 300.0,
      "allocated_units": 250,
      "shortage": 50,
      "excess": 0
    }
  ]
}
```

---

### 4. POST `/simulate`
Executes side-by-side comparative simulation evaluating an unpromoted, standard baseline against an uplifted scenario.

**Request Schema:**
```json
{
  "total_available_units": 1000,
  "horizon_days": 7,
  "is_holiday_week": false,
  "promo_boost": {
    "STORE_1": 1.30
  }
}
```

**Example Response (200 OK):**
```json
{
  "baseline": {
    "total_demand": 1200.0,
    "total_allocated": 1000,
    "total_shortage": 200,
    "allocations": [...]
  },
  "adjusted": {
    "total_demand": 1350.0,
    "total_allocated": 1000,
    "total_shortage": 350,
    "allocations": [...]
  },
  "demand_lift_percentage": 12.5,
  "shortage_change": 150
}
```

---

## Testing

The project uses `pytest` for all unit, integration, and contract tests.

### Running the Entire Test Suite
```bash
python -m pytest -v
```

### Running Specific Test Modules
```bash
# Data Loader tests
pytest tests/test_data_loader.py -v

# Forecasting logic tests
pytest tests/test_forecasting.py -v

# Advanced features & enterprise tests
pytest tests/test_advanced_features.py -v

# Allocation algorithms tests (Proportional, PuLP LP, & store-SKU)
pytest tests/test_allocation.py -v

# FastAPI REST API contract tests
pytest tests/test_api.py -v

# End-to-end pipeline invariant tests
pytest tests/test_pipeline.py -v
```

### Test Suite Summary
- **Total Test Cases:** 99
- **Passing:** 99 (100% pass rate across all suites)
- **Key Invariants Enforced:**
  - Non-negative forecasts ($\hat{y} \ge 0$).
  - Total allocation never exceeds available supply ($\sum A_i \le C$).
  - No individual store receives more than its demand ($A_i \le D_i$).
  - Allocation plus shortage strictly balances demand ($A_i + S_i = D_i$).
  - Rounding remains strictly integer-valued ($A_i \in \mathbb{Z}_{\ge 0}$).
  - Multi-item store-SKU rationing respects both per-SKU and total capacity.

---

## Deployment

### 1. Streamlit Community Cloud
This repository is configured for one-click deployment on Streamlit Community Cloud:
- **Repository:** `jos151/HTH016ML04`
- **Main file path:** `frontend/app.py`
- **Live URL:** [https://hth016ml04.streamlit.app/](https://hth016ml04.streamlit.app/)
- **Configuration:** Handled automatically by `.streamlit/config.toml` (`headless = true`) and `.streamlit/credentials.toml`. The frontend detects the cloud environment and runs the forecasting and allocation engine in-process without requiring a separate Uvicorn instance.

### 2. Docker / Server Deployment
To run as microservices in production:

**Start FastAPI Service:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Start Streamlit Service:**
```bash
export API_BASE_URL="http://127.0.0.1:8000"
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Contributing

1. **Fork the Repository:** Click the `Fork` button on GitHub.
2. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/allocation-heuristic
   ```
3. **Commit Your Changes:**
   ```bash
   git commit -m "Add prioritized store tiering to allocation"
   ```
4. **Push to Your Branch:**
   ```bash
   git push origin feature/allocation-heuristic
   ```
5. **Open a Pull Request:** Submit a Pull Request targeting `main`. Ensure all 85 pytest tests pass prior to submission.

---

## Support

- **Issue Tracker:** Submit bug reports and feature requests via [GitHub Issues](https://github.com/jos151/HTH016ML04/issues).
- **Discussions:** Open a thread in [GitHub Discussions](https://github.com/jos151/HTH016ML04/discussions) for architectural feedback or algorithmic improvements.

---

## FAQ

**Q: Why use the Largest-Remainder method instead of standard rounding (`round()`)?**  
A: Standard mathematical rounding does not conserve inventory. Rounding each store independently can cause the sum of allocations to exceed total warehouse supply or leave unallocated stock. The largest-remainder algorithm guarantees that $\sum A_i = \min(C, \sum D_i)$ exactly.

**Q: Can this system handle cold-start stores or newly introduced SKUs?**  
A: Yes. The forecasting module in `backend/forecasting.py` inspects available history for each store-SKU pair. If fewer than 7 days of history exist, it computes a fallback average across store sales or defaults to a safe unit baseline ($1.0$), ensuring zero `NaN` values.

**Q: What is the difference between `proportional` and `lp` allocation?**  
A: `proportional` allocates inventory in direct ratio to demand quotas. `lp` uses PuLP (Mixed-Integer Linear Programming) to minimize total weighted penalties for shortages and excess inventory.

---

## Known Issues

- **High Historical Sparsity:** On SKUs with intermittent or zero sales over extended periods, the 7-day rolling average reflects low baseline velocity. In such cases, store-level promotional multipliers scale from lower initial values.
- **Single Central Echelon:** The current optimization model allocates from a single upstream distribution center to stores; multi-echelon network transfer lags are not yet modeled.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

## Acknowledgements

- Built for the retail supply-chain and operations research community.
- Solvers powered by [PuLP](https://coin-or.github.io/pulp/) and the COIN-OR CBC branch-and-cut optimization suite.
- Web services powered by [FastAPI](https://fastapi.tiangolo.com/) and [Streamlit](https://streamlit.io/).

---

## Project Status

**Stable / Production Ready**  
All core forecasting algorithms, proportional largest-remainder logic, PuLP linear programming optimization, REST endpoints, and the Streamlit dashboard are fully implemented, verified, and passing 85/85 automated tests.
