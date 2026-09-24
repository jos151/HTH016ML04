"""
Automated tests for advanced platform capabilities:
- Empirical forecast uncertainty bounds
- Store-SKU level constrained allocation
- Safety stock and reorder point planning
- Allocation fairness & business cost impact
- Data quality monitoring & Excel report exports
- New REST API endpoints
"""

from io import BytesIO
import openpyxl
import pandas as pd
import pytest
from starlette.testclient import TestClient

from backend.data_loader import load_demand_data, get_data_quality_report, validate_uploaded_sales_data
from backend.forecasting import forecast_demand_with_bounds
from backend.allocation import allocate_sku_inventory
from backend.inventory_planning import (
    calculate_safety_stock_and_reorder,
    calculate_business_cost_impact,
    calculate_allocation_fairness,
)
from backend.reports import generate_excel_report, generate_inventory_template
from backend.main import app

client = TestClient(app)


def test_forecast_demand_with_bounds():
    df = load_demand_data()
    fc = forecast_demand_with_bounds(df, horizon_days=7, confidence_level=0.90)

    assert not fc.empty
    assert "lower_confidence_bound" in fc.columns
    assert "upper_confidence_bound" in fc.columns
    assert "uncertainty_risk" in fc.columns

    for _, r in fc.iterrows():
        pred = r["predicted_units"]
        low = r["lower_confidence_bound"]
        high = r["upper_confidence_bound"]
        risk = r["uncertainty_risk"]

        assert low <= pred + 1e-4
        assert high >= pred - 1e-4
        assert low >= 0.0
        assert risk in ["Low", "Medium", "High"]


def test_allocate_sku_inventory():
    df = load_demand_data()
    fc = forecast_demand_with_bounds(df, horizon_days=7)

    # Allocate with 1000 total inventory
    sku_alloc = allocate_sku_inventory(
        forecast_df=fc,
        total_available_units=1000,
        allocation_method="proportional",
    )

    assert not sku_alloc.empty
    expected_cols = [
        "warehouse_id", "allocation_date", "store_id", "sku_id",
        "forecasted_demand", "available_sku_inventory", "allocated_units",
        "shortage", "excess", "fulfillment_percentage", "allocation_method", "priority_weight"
    ]
    for c in expected_cols:
        assert c in sku_alloc.columns

    # Invariants
    assert (sku_alloc["allocated_units"] >= 0).all()
    assert (sku_alloc["shortage"] >= 0).all()
    assert (sku_alloc["allocated_units"] <= sku_alloc["forecasted_demand"]).all()
    assert (sku_alloc["allocated_units"] + sku_alloc["shortage"] == sku_alloc["forecasted_demand"]).all()
    assert sku_alloc["allocated_units"].sum() <= 1000


def test_safety_stock_and_reorder():
    df = load_demand_data()
    recs = calculate_safety_stock_and_reorder(
        historical_df=df,
        lead_time_days=7,
        target_service_level=0.95,
        min_order_qty=10,
        pack_size=5,
    )

    assert not recs.empty
    assert len(recs) == df["sku_id"].nunique()

    for _, r in recs.iterrows():
        assert r["safety_stock"] >= 0
        assert r["reorder_point"] >= r["safety_stock"]
        assert r["urgency"] in ["Immediate reorder", "Reorder soon", "Monitor", "No action"]
        assert len(r["recommended_action"]) > 0


def test_business_cost_impact():
    cost = calculate_business_cost_impact(
        total_demand=1200,
        total_allocated=1000,
        total_shortage=200,
        total_excess=0,
        remaining_inventory=0,
        shortage_cost_per_unit=1.0,
        overstock_cost_per_unit=0.3,
        unit_selling_price=25.0,
        unit_cost=15.0,
    )

    assert cost["shortage_cost"] == 200.0
    assert cost["lost_revenue"] == 5000.0
    assert cost["lost_margin"] == 2000.0
    assert cost["fulfilled_revenue"] == 25000.0


def test_allocation_fairness():
    df_alloc = pd.DataFrame({
        "store_id": ["STORE_A", "STORE_B", "STORE_C"],
        "forecasted_demand": [500, 400, 300],
        "allocated_units": [417, 333, 250],
        "shortage": [83, 67, 50],
        "excess": [0, 0, 0],
    })
    fair = calculate_allocation_fairness(df_alloc)

    assert 0.0 <= fair["fairness_score"] <= 1.0
    assert fair["min_fulfillment_pct"] <= fair["avg_fulfillment_pct"] <= fair["max_fulfillment_pct"]


def test_data_quality_report():
    report = get_data_quality_report()
    assert report["status"] in ["Passed", "Passed with warnings"]
    assert report["row_count"] == 36550
    assert report["store_count"] == 5
    assert report["sku_count"] == 10
    assert report["duplicate_count"] == 0
    assert report["negative_sales_count"] == 0


def test_validate_uploaded_sales_data():
    valid_csv = (
        "date,store_id,sku_id,units_sold\n"
        "2023-01-01,STORE_1,SKU_01,15\n"
        "2023-01-02,STORE_1,SKU_01,20\n"
    ).encode("utf-8")
    res = validate_uploaded_sales_data(valid_csv, "test_upload.csv")
    assert res["valid"] is True
    assert res["row_count"] == 2

    invalid_csv = "date,store_id\n2023-01-01,STORE_1\n".encode("utf-8")
    res_inv = validate_uploaded_sales_data(invalid_csv, "bad.csv")
    assert res_inv["valid"] is False
    assert len(res_inv["errors"]) > 0


def test_generate_excel_report():
    df = load_demand_data()
    fc = forecast_demand_with_bounds(df, horizon_days=7)
    sku_alloc = allocate_sku_inventory(fc, total_available_units=1000)
    store_alloc = sku_alloc.groupby("store_id", as_index=False).agg({
        "forecasted_demand": "sum",
        "allocated_units": "sum",
        "shortage": "sum",
        "excess": "sum",
    })

    excel_bytes = generate_excel_report(
        forecast_df=fc,
        allocation_df=store_alloc,
        sku_allocation_df=sku_alloc,
    )
    assert len(excel_bytes) > 0

    wb = openpyxl.load_workbook(BytesIO(excel_bytes))
    sheet_names = wb.sheetnames
    expected_sheets = [
        "Executive_Summary", "Forecast_Details", "Allocation_Details",
        "Store_Summary", "SKU_Summary", "Shortage_Risk",
        "Scenario_Assumptions", "Validation_Checks"
    ]
    for s in expected_sheets:
        assert s in sheet_names


def test_api_metadata_endpoints():
    r_meta = client.get("/metadata")
    assert r_meta.status_code == 200
    data = r_meta.json()
    assert "stores" in data and len(data["stores"]) == 5
    assert "skus" in data and len(data["skus"]) == 10
    assert "categories" in data

    r_stores = client.get("/stores")
    assert r_stores.status_code == 200
    assert len(r_stores.json()) == 5

    r_skus = client.get("/skus")
    assert r_skus.status_code == 200
    assert len(r_skus.json()) == 10


def test_api_forecast_bounds():
    r = client.get("/forecast/bounds?horizon_days=7&confidence_level=0.90")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 5 * 10 * 7
    assert "lower_confidence_bound" in items[0]
    assert "upper_confidence_bound" in items[0]
    assert "uncertainty_risk" in items[0]


def test_api_sku_allocate():
    payload = {
        "total_available_units": 1000,
        "method": "proportional",
        "horizon_days": 7,
    }
    r = client.post("/allocate/sku", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert len(data["allocations"]) > 0
    assert "summary" in data


def test_api_safety_stock():
    payload = {
        "lead_time_days": 7,
        "target_service_level": 0.95,
    }
    r = client.post("/safety-stock", json=payload)
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert len(recs) == 10


def test_api_data_quality():
    r = client.get("/data-quality")
    assert r.status_code == 200
    dq = r.json()
    assert dq["status"] in ["Passed", "Passed with warnings"]
    assert dq["store_count"] == 5


def test_api_reports_export():
    payload = {
        "total_available_units": 1000,
        "method": "proportional",
        "horizon_days": 7,
    }
    r = client.post("/reports/export", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(r.content) > 1000
