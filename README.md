# Demand Forecasting & Inventory Allocation

A minimal retail demand forecasting and inventory allocation pipeline.

## Project Structure

```text
├── backend/
│   ├── allocation.py     # Inventory allocation and optimization (PuLP)
│   ├── data_loader.py    # Demand data ingestion, filtering, and reshaping
│   ├── forecasting.py   # Demand forecasting models
│   ├── main.py           # FastAPI service entrypoint
│   └── models.py         # Data schemas and domain models
├── data/
│   └── sales.csv         # Sales demand data (M5 Walmart / Rossmann format)
├── frontend/
│   └── app.py            # Streamlit dashboard interface
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Setup

```bash
pip install -r requirements.txt
```

## Running Data Loader

```bash
python backend/data_loader.py
```
