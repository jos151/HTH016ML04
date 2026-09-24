# Demand Forecasting & Inventory Allocation

A retail demand forecasting and inventory allocation pipeline featuring a standalone Streamlit web dashboard and an optional FastAPI service.

## Project Structure

```text
HTH016ML04/
├── backend/
│   ├── __init__.py       # Package marker
│   ├── allocation.py     # Inventory allocation and optimization (PuLP)
│   ├── data_loader.py    # Demand data ingestion, filtering, and reshaping
│   ├── forecasting.py   # Demand forecasting models (7-day MA + seasonality)
│   ├── main.py           # FastAPI service entrypoint (optional API)
│   └── models.py         # Data schemas and domain models
├── frontend/
│   ├── __init__.py       # Package marker
│   └── app.py            # Streamlit dashboard interface (Cloud entrypoint)
├── data/
│   └── sales.csv         # Sales demand data (M5 Walmart / Rossmann format)
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---

## Running Locally

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Streamlit Application

```bash
streamlit run frontend/app.py
```

The Streamlit dashboard runs standalone by directly calling the backend analytics and optimization modules. No separate backend process is required.

### 3. Optional: Run FastAPI Backend

If you wish to expose the REST API for third-party integrations:

```bash
python -m uvicorn backend.main:app --port 8000 --reload
```

---

## Streamlit Community Cloud Deployment

This project is configured to run out of the box on [Streamlit Community Cloud](https://share.streamlit.io):

| Setting | Value |
| --- | --- |
| **Repository** | `jos151/HTH016ML04` |
| **Branch** | `main` |
| **Main file path** | `frontend/app.py` |

### Architecture on Streamlit Cloud
The Streamlit application imports and executes the backend logic directly in-process:
- `backend.data_loader.load_demand_data` loads `data/sales.csv`
- `backend.forecasting.forecast_demand` generates 7-day demand projections
- `backend.allocation.allocate_inventory` & `allocate_inventory_lp` compute optimal stock distribution

**No external FastAPI server or `127.0.0.1:8000` process is needed for Streamlit Cloud deployment.**
