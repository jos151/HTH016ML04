import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.data_loader import (
    load_demand_data,
    STORE_IDS,
    SKU_IDS,
    get_data_quality_report,
    validate_uploaded_sales_data,
)
from backend.forecasting import (
    forecast_demand,
    forecast_demand_with_bounds,
    calculate_forecast_metrics,
)
from backend.allocation import (
    allocate_inventory,
    allocate_inventory_lp,
    allocate_sku_inventory,
    get_allocation_summary,
)
from backend.inventory_planning import (
    calculate_safety_stock_and_reorder,
    calculate_business_cost_impact,
    calculate_allocation_fairness,
)
from backend.reports import generate_excel_report, generate_inventory_template
from backend.models import (
    HealthResponse,
    ForecastItem,
    ForecastItemWithBounds,
    AllocationRequest,
    AllocationResponse,
    SkuAllocationRequest,
    SkuAllocationResponse,
    SkuAllocationItem,
    SimulationRequest,
    SimulationResponse,
    ScenarioResult,
    StoreAllocationResult,
    AllocationSummary,
    SafetyStockRequest,
    SafetyStockResponse,
    SafetyStockItem,
    DataQualityResponse,
    MetadataResponse,
    ErrorResponse,
    CategoryItem,
    CategoriesResponse,
    HistoryRecordItem,
    HistorySummary,
    HistoryResponse,
    MobileForecastRequest,
    MobileForecastItem,
    ForecastSummary,
    MobileForecastResponse,
    ScenarioInput,
    CompareScenariosRequest,
    ScenarioMetricItem,
    ScenarioComparisonSummary,
    CompareScenariosResponse,
    SkuModelMetric,
    OverallModelMetrics,
    ModelMetricsResponse,
)

app = FastAPI(
    title="Inventory-Constrained Demand Forecasting and Allocation API",
    description="REST API for store-SKU demand forecasting, proportional inventory allocation, and scenario simulation.",
    version="1.1.0",
)

# Permissive CORS middleware for local hackathon and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product catalog category mapping for project SKUs
SKU_CATEGORY_MAP: Dict[str, str] = {
    "SKU_01": "Electronics",
    "SKU_02": "Electronics",
    "SKU_03": "Apparel",
    "SKU_04": "Apparel",
    "SKU_05": "Home & Kitchen",
    "SKU_06": "Home & Kitchen",
    "SKU_07": "Grocery",
    "SKU_08": "Grocery",
    "SKU_09": "Health & Personal Care",
    "SKU_10": "Health & Personal Care",
}

CATEGORY_METADATA = [
    {"category_id": "CAT_01", "name": "Electronics", "skus": ["SKU_01", "SKU_02"]},
    {"category_id": "CAT_02", "name": "Apparel", "skus": ["SKU_03", "SKU_04"]},
    {"category_id": "CAT_03", "name": "Home & Kitchen", "skus": ["SKU_05", "SKU_06"]},
    {"category_id": "CAT_04", "name": "Grocery", "skus": ["SKU_07", "SKU_08"]},
    {"category_id": "CAT_05", "name": "Health & Personal Care", "skus": ["SKU_09", "SKU_10"]},
]


# =====================================================================
# Standardized Error Handling Middleware / Exception Handlers
# =====================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into the standard mobile error schema."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    loc = first_error.get("loc", [])
    field_name = str(loc[-1]) if loc else None
    msg = first_error.get("msg", "Invalid request payload.")

    code = "VALIDATION_ERROR"
    if field_name:
        fn_lower = field_name.lower()
        if "inventory" in fn_lower:
            code = "INVALID_INVENTORY"
        elif "horizon" in fn_lower:
            code = "INVALID_HORIZON"
        elif "promo" in fn_lower:
            code = "INVALID_PROMOTION"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": code,
            "message": msg,
            "field": field_name,
            "details": [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")} for e in errors],
            "request_id": request.headers.get("x-request-id"),
            "detail": f"{msg} (got: {first_error.get('input', '')})" if first_error.get("input") is not None else msg,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats HTTP exceptions without exposing filesystem paths or stack traces."""
    raw_msg = str(exc.detail)
    clean_msg = re.sub(r'[A-Za-z]:\\[^ \t\n\r]+', '[file]', raw_msg)

    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_400_BAD_REQUEST:
        code = "BAD_REQUEST"
        low = clean_msg.lower()
        if "inventory" in low:
            code = "INVALID_INVENTORY"
        elif "promo" in low:
            code = "INVALID_PROMOTION"
        elif "horizon" in low:
            code = "INVALID_HORIZON"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        code = "VALIDATION_ERROR"
    elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        code = "SERVICE_UNAVAILABLE"
    elif exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        code = "INTERNAL_SERVER_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": code,
            "message": clean_msg,
            "field": None,
            "details": None,
            "request_id": request.headers.get("x-request-id"),
            "detail": clean_msg,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Shields clients from raw server errors and stack traces."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred while processing the request.",
            "field": None,
            "details": None,
            "request_id": request.headers.get("x-request-id"),
            "detail": "An internal server error occurred while processing the request.",
        },
    )


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns application status and demand dataset metadata."""
    try:
        df = load_demand_data()
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty or uninitialized.",
            )

        return HealthResponse(
            status="ok",
            data_loaded=True,
            row_count=len(df),
            store_count=int(df["store_id"].nunique()),
            sku_count=int(df["sku_id"].nunique()),
            minimum_date=str(df["date"].min()),
            maximum_date=str(df["date"].max()),
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Source dataset missing: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check error: {exc}",
        )


@app.get("/forecast", response_model=List[ForecastItem])
def get_forecast(
    horizon_days: int = Query(default=7, ge=1, le=365, description="Number of days to forecast"),
    is_holiday_week: bool = Query(default=False, description="Apply +15% holiday uplift"),
    promotion_store: Optional[str] = Query(default=None, description="Optional store ID to boost"),
    promotion_multiplier: Optional[float] = Query(default=None, description="Promotional multiplier (must be >= 1.0)"),
) -> List[ForecastItem]:
    """Generates demand forecasts for all stores and SKUs across horizon_days."""
    if horizon_days <= 0 or horizon_days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid horizon_days={horizon_days}. Must be between 1 and 365.",
        )

    promo_boost = None
    if promotion_store is not None or promotion_multiplier is not None:
        if promotion_store is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="promotion_store must be provided when promotion_multiplier is specified.",
            )
        if promotion_multiplier is None:
            promotion_multiplier = 1.30

        if promotion_multiplier < 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"promotion_multiplier must be at least 1.0, got {promotion_multiplier}",
            )

        promo_boost = {promotion_store: float(promotion_multiplier)}

    try:
        raw_df = load_demand_data()
        if raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        # Validate promotion_store existence if supplied
        if promo_boost:
            valid_stores = set(raw_df["store_id"].unique())
            for p_store in promo_boost.keys():
                if p_store not in valid_stores:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown promotion store '{p_store}'. Must be one of: {sorted(list(valid_stores))}",
                    )

        forecast_df = forecast_demand(
            df=raw_df,
            horizon_days=horizon_days,
            promo_boost=promo_boost,
            is_holiday_week=is_holiday_week,
        )
        return forecast_df.to_dict(orient="records")
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Source dataset missing: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting calculation failed: {exc}",
        )


@app.post("/allocate", response_model=AllocationResponse)
def post_allocate(payload: AllocationRequest) -> AllocationResponse:
    """Allocates inventory across stores based on forecasted demand and supply constraint."""
    if payload.total_available_units < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="total_available_units must be non-negative (>= 0).",
        )

    if payload.method not in ["proportional", "lp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown allocation method '{payload.method}'. Supported methods: ['proportional', 'lp'].",
        )

    try:
        raw_df = load_demand_data()
        if raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        if payload.promo_boost:
            valid_stores = set(raw_df["store_id"].unique())
            for p_store in payload.promo_boost.keys():
                if p_store not in valid_stores:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown store '{p_store}' in promo_boost. Valid stores: {sorted(list(valid_stores))}",
                    )

        forecast_df = forecast_demand(
            df=raw_df,
            horizon_days=payload.horizon_days,
            promo_boost=payload.promo_boost,
            is_holiday_week=payload.is_holiday_week,
        )

        if payload.method == "lp":
            allocation_df = allocate_inventory_lp(
                forecast_df=forecast_df,
                total_available_units=payload.total_available_units,
                shortage_cost=payload.shortage_cost if payload.shortage_cost is not None else 1.0,
                overstock_cost=payload.overstock_cost if payload.overstock_cost is not None else 0.3,
                fallback_on_solver_error=True,
            )
        else:
            allocation_df = allocate_inventory(
                forecast_df=forecast_df,
                total_available_units=payload.total_available_units,
            )

        sku_records = None
        if payload.include_sku_breakdown or payload.inventory_by_sku or payload.store_priorities or payload.sku_priorities:
            sku_alloc_df = allocate_sku_inventory(
                forecast_df=forecast_df,
                inventory_by_sku=payload.inventory_by_sku,
                total_available_units=payload.total_available_units,
                store_priorities=payload.store_priorities,
                sku_priorities=payload.sku_priorities,
                allocation_method=payload.method,
            )
            sku_records = [SkuAllocationItem(**r) for r in sku_alloc_df.to_dict(orient="records")]

        summary_dict = allocation_df.attrs.get(
            "summary",
            get_allocation_summary(allocation_df, payload.total_available_units),
        )

        alloc_records = allocation_df.to_dict(orient="records")
        return AllocationResponse(
            allocations=[StoreAllocationResult(**r) for r in alloc_records],
            summary=AllocationSummary(**summary_dict),
            sku_allocations=sku_records,
            method=payload.method,
            unit="units",
            dataset_source="data/processed/sales.csv",
            is_real_data=True,
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Source dataset missing: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Allocation process failed: {exc}",
        )


@app.post("/simulate", response_model=SimulationResponse)
def post_simulate(payload: SimulationRequest) -> SimulationResponse:
    """Compares a standard baseline scenario against an adjusted (promo/holiday) scenario."""
    try:
        raw_df = load_demand_data()
        if raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        if payload.promo_boost:
            valid_stores = set(raw_df["store_id"].unique())
            for p_store in payload.promo_boost.keys():
                if p_store not in valid_stores:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown store '{p_store}' in promo_boost. Valid stores: {sorted(list(valid_stores))}",
                    )

        supply = payload.total_available_units if payload.total_available_units is not None else 1000.0

        # 1. Baseline scenario (no promo boost, no holiday)
        base_forecast = forecast_demand(
            df=raw_df,
            horizon_days=payload.horizon_days,
            promo_boost=None,
            is_holiday_week=False,
        )
        base_alloc = allocate_inventory(base_forecast, total_available_units=supply)
        base_summary = base_alloc.attrs.get("summary", get_allocation_summary(base_alloc, supply))

        base_scenario = ScenarioResult(
            scenario_name="Baseline (No Event / Standard Promotion)",
            total_demand=base_summary["total_forecasted_demand"],
            total_allocated=base_summary["total_allocated_units"],
            total_shortage=base_summary["total_shortage"],
            allocations=[StoreAllocationResult(**r) for r in base_alloc.to_dict(orient="records")],
            forecast_preview=[ForecastItem(**r) for r in base_forecast.head(5).to_dict(orient="records")],
        )

        # 2. Adjusted scenario (with promo_boost and/or holiday)
        adj_forecast = forecast_demand(
            df=raw_df,
            horizon_days=payload.horizon_days,
            promo_boost=payload.promo_boost,
            is_holiday_week=payload.is_holiday_week,
        )
        adj_alloc = allocate_inventory(adj_forecast, total_available_units=supply)
        adj_summary = adj_alloc.attrs.get("summary", get_allocation_summary(adj_alloc, supply))

        scenario_label = []
        if payload.promo_boost:
            scenario_label.append(f"Promo({list(payload.promo_boost.keys())})")
        if payload.is_holiday_week:
            scenario_label.append("Holiday(+15%)")
        label_str = " + ".join(scenario_label) if scenario_label else "Standard Baseline"

        adj_scenario = ScenarioResult(
            scenario_name=f"Adjusted: {label_str}",
            total_demand=adj_summary["total_forecasted_demand"],
            total_allocated=adj_summary["total_allocated_units"],
            total_shortage=adj_summary["total_shortage"],
            allocations=[StoreAllocationResult(**r) for r in adj_alloc.to_dict(orient="records")],
            forecast_preview=[ForecastItem(**r) for r in adj_forecast.head(5).to_dict(orient="records")],
        )

        # Lift and shortage change
        base_d = base_summary["total_forecasted_demand"]
        adj_d = adj_summary["total_forecasted_demand"]
        lift_pct = round(((adj_d - base_d) / base_d) * 100.0, 2) if base_d > 0 else 0.0
        shortage_diff = round(adj_summary["total_shortage"] - base_summary["total_shortage"], 2)

        return SimulationResponse(
            baseline=base_scenario,
            adjusted=adj_scenario,
            demand_lift_percentage=lift_pct,
            shortage_change=shortage_diff,
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Source dataset missing: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {exc}",
        )


@app.get("/metadata", response_model=MetadataResponse)
def get_metadata() -> MetadataResponse:
    """Returns catalog of active stores, SKUs, product categories, and date bounds."""
    try:
        df = load_demand_data()
        stores = sorted(df["store_id"].unique().tolist())
        skus = sorted(df["sku_id"].unique().tolist())
        # Canonical retail categories associated with project SKUs
        categories = ["Electronics", "Apparel", "Home & Kitchen", "Grocery", "Health & Personal Care"]
        return MetadataResponse(
            stores=stores,
            skus=skus,
            categories=categories,
            min_date=str(df["date"].min()),
            max_date=str(df["date"].max()),
            total_rows=int(len(df)),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metadata: {exc}",
        )


@app.get("/stores", response_model=List[str])
def get_stores() -> List[str]:
    """Returns active store identifiers."""
    try:
        df = load_demand_data()
        return sorted(df["store_id"].unique().tolist())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stores: {exc}",
        )


@app.get("/skus", response_model=List[str])
def get_skus() -> List[str]:
    """Returns active SKU identifiers."""
    try:
        df = load_demand_data()
        return sorted(df["sku_id"].unique().tolist())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch SKUs: {exc}",
        )


@app.get(
    "/categories",
    response_model=CategoriesResponse,
    summary="Get product categories",
    description="Returns product categories and their associated SKU lists.",
)
def get_categories() -> CategoriesResponse:
    """Returns product categories, SKU associations, and total counts."""
    items = [
        CategoryItem(
            category_id=c["category_id"],
            name=c["name"],
            sku_count=len(c["skus"]),
            skus=c["skus"],
        )
        for c in CATEGORY_METADATA
    ]
    return CategoriesResponse(total=len(items), categories=items)


@app.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get paginated historical demand records",
    description="Returns filtered and paginated historical POS demand records with summary aggregates.",
)
def get_history(
    page: int = Query(default=1, ge=1, description="1-based page index"),
    page_size: int = Query(default=50, ge=1, le=500, description="Records per page"),
    store_id: Optional[str] = Query(default=None, description="Filter by store ID"),
    sku_id: Optional[str] = Query(default=None, description="Filter by SKU ID"),
    category: Optional[str] = Query(default=None, description="Filter by category name"),
    start_date: Optional[str] = Query(default=None, description="Filter on or after ISO date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Filter on or before ISO date (YYYY-MM-DD)"),
) -> HistoryResponse:
    """Provides mobile clients with bounded, filtered historical sales records and aggregates."""
    try:
        df = load_demand_data()
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        filtered = df.copy()
        if store_id:
            filtered = filtered[filtered["store_id"] == store_id]
        if sku_id:
            filtered = filtered[filtered["sku_id"] == sku_id]
        if category:
            matching_skus = [s for s, c in SKU_CATEGORY_MAP.items() if c.lower() == category.lower()]
            filtered = filtered[filtered["sku_id"].isin(matching_skus)]
        if start_date:
            filtered = filtered[filtered["date"] >= start_date]
        if end_date:
            filtered = filtered[filtered["date"] <= end_date]

        total_matching = len(filtered)
        if total_matching > 0:
            tot_units = round(float(filtered["units_sold"].sum()), 2)
            avg_units = round(float(filtered["units_sold"].mean()), 2)
            min_d = str(filtered["date"].min())
            max_d = str(filtered["date"].max())
            d_stores = int(filtered["store_id"].nunique())
            d_skus = int(filtered["sku_id"].nunique())
        else:
            tot_units = 0.0
            avg_units = 0.0
            min_d = ""
            max_d = ""
            d_stores = 0
            d_skus = 0

        summary = HistorySummary(
            total_records=total_matching,
            total_units_sold=tot_units,
            average_units_per_record=avg_units,
            min_date=min_d,
            max_date=max_d,
            distinct_stores=d_stores,
            distinct_skus=d_skus,
        )

        total_pages = max(1, math.ceil(total_matching / page_size))
        offset = (page - 1) * page_size
        page_df = filtered.iloc[offset : offset + page_size]

        items: List[HistoryRecordItem] = []
        for _, row in page_df.iterrows():
            d_str = str(row["date"])
            dt = pd.to_datetime(d_str)
            sku = str(row["sku_id"])
            items.append(
                HistoryRecordItem(
                    date=d_str,
                    store_id=str(row["store_id"]),
                    sku_id=sku,
                    category=SKU_CATEGORY_MAP.get(sku, "General"),
                    units_sold=round(float(row["units_sold"]), 2),
                    day_of_week=dt.day_name(),
                    is_weekend=bool(dt.dayofweek >= 5),
                )
            )

        return HistoryResponse(
            items=items,
            total=total_matching,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            summary=summary,
            dataset_source="data/processed/sales.csv (Retail Store POS Transactions)",
            is_real_data=True,
            unit="units",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical data: {exc}",
        )


@app.post(
    "/forecast",
    response_model=MobileForecastResponse,
    summary="Generate mobile demand forecast with uncertainty bounds",
    description="Calculates store-SKU demand forecasts with moving average baseline, DOW seasonality, promo multipliers, holiday lift, and empirical confidence bounds.",
)
def post_forecast(payload: MobileForecastRequest) -> MobileForecastResponse:
    """Generates demand forecasts with bounds, filtering, and summary statistics."""
    try:
        raw_df = load_demand_data()
        if raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        if payload.promo_boost:
            valid_stores = set(raw_df["store_id"].unique())
            for p_store in payload.promo_boost.keys():
                if p_store not in valid_stores:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown promotion store '{p_store}'. Must be one of: {sorted(list(valid_stores))}",
                    )

        conf_level = payload.confidence_level if payload.confidence_level is not None else 0.90
        fc_df = forecast_demand_with_bounds(
            df=raw_df,
            horizon_days=payload.horizon_days,
            promo_boost=payload.promo_boost,
            is_holiday_week=payload.is_holiday_week,
            confidence_level=conf_level,
        )

        if payload.stores:
            fc_df = fc_df[fc_df["store_id"].isin(payload.stores)]
        if payload.skus:
            fc_df = fc_df[fc_df["sku_id"].isin(payload.skus)]
        if payload.categories:
            matching_skus = set()
            for cat in payload.categories:
                matching_skus.update([s for s, c in SKU_CATEGORY_MAP.items() if c.lower() == cat.lower()])
            fc_df = fc_df[fc_df["sku_id"].isin(matching_skus)]
        if payload.start_date:
            fc_df = fc_df[fc_df["forecast_date"] >= payload.start_date]
        if payload.end_date:
            fc_df = fc_df[fc_df["forecast_date"] <= payload.end_date]

        items: List[MobileForecastItem] = []
        for _, row in fc_df.iterrows():
            sku = str(row["sku_id"])
            items.append(
                MobileForecastItem(
                    store_id=str(row["store_id"]),
                    sku_id=sku,
                    category=SKU_CATEGORY_MAP.get(sku, "General"),
                    forecast_date=str(row["forecast_date"]),
                    baseline_units=float(row["baseline_units"]),
                    promo_multiplier=float(row["promo_multiplier"]),
                    holiday_multiplier=float(row["holiday_multiplier"]),
                    predicted_units=float(row["predicted_units"]),
                    lower_confidence_bound=float(row["lower_confidence_bound"]),
                    upper_confidence_bound=float(row["upper_confidence_bound"]),
                    confidence_level=float(row["confidence_level"]),
                    uncertainty_risk=str(row["uncertainty_risk"]),
                )
            )

        tot_base = round(sum(i.baseline_units for i in items), 2)
        tot_pred = round(sum(i.predicted_units for i in items), 2)
        days = payload.horizon_days if payload.horizon_days > 0 else 1
        avg_daily = round(tot_pred / days, 2)
        d_stores = len({i.store_id for i in items})
        d_skus = len({i.sku_id for i in items})
        start_d = min((i.forecast_date for i in items), default="")
        end_d = max((i.forecast_date for i in items), default="")

        summary = ForecastSummary(
            total_baseline_units=tot_base,
            total_predicted_units=tot_pred,
            average_daily_units=avg_daily,
            distinct_stores=d_stores,
            distinct_skus=d_skus,
            forecast_start_date=start_d,
            forecast_end_date=end_d,
        )

        return MobileForecastResponse(
            forecast_items=items,
            summary=summary,
            horizon_days=payload.horizon_days,
            is_holiday_week=payload.is_holiday_week,
            model_name="7-Day Moving Average with DOW Seasonality",
            algorithm="Moving Average + Multiplicative Day-of-Week Seasonality",
            dataset_source="data/processed/sales.csv (Retail Store POS Transactions)",
            is_real_data=True,
            unit="units",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting calculation failed: {exc}",
        )


@app.post(
    "/compare-scenarios",
    response_model=CompareScenariosResponse,
    summary="Compare multiple inventory and promotion scenarios",
    description="Simulates and compares key demand and allocation metrics across 2 to 10 what-if scenarios simultaneously.",
)
def post_compare_scenarios(payload: CompareScenariosRequest) -> CompareScenariosResponse:
    """Runs parallel scenario projections and summarizes relative outcomes."""
    try:
        raw_df = load_demand_data()
        if raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        metric_items: List[ScenarioMetricItem] = []
        for sc in payload.scenarios:
            if sc.promo_boost:
                valid_stores = set(raw_df["store_id"].unique())
                for s in sc.promo_boost.keys():
                    if s not in valid_stores:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unknown store '{s}' in scenario '{sc.scenario_name}' promo_boost.",
                        )

            fc = forecast_demand(
                df=raw_df,
                horizon_days=sc.horizon_days,
                promo_boost=sc.promo_boost,
                is_holiday_week=sc.is_holiday_week,
            )

            if sc.method == "lp":
                alloc_df = allocate_inventory_lp(
                    fc,
                    total_available_units=sc.total_available_units,
                    fallback_on_solver_error=True,
                )
            else:
                alloc_df = allocate_inventory(fc, total_available_units=sc.total_available_units)

            sm = alloc_df.attrs.get("summary", get_allocation_summary(alloc_df, sc.total_available_units))
            dem = float(sm["total_forecasted_demand"])
            alloc_u = float(sm["total_allocated_units"])
            short_u = float(sm["total_shortage"])
            excess_u = float(sm["total_excess"])
            f_rate = round((alloc_u / dem * 100.0), 2) if dem > 0 else 100.0
            s_rate = round((short_u / dem * 100.0), 2) if dem > 0 else 0.0

            store_records = [StoreAllocationResult(**r) for r in alloc_df.to_dict(orient="records")]
            metric_items.append(
                ScenarioMetricItem(
                    scenario_name=sc.scenario_name,
                    horizon_days=sc.horizon_days,
                    total_available_units=sc.total_available_units,
                    total_forecasted_demand=dem,
                    total_allocated_units=alloc_u,
                    total_shortage=short_u,
                    total_excess=excess_u,
                    fulfillment_rate_percentage=f_rate,
                    shortage_percentage=s_rate,
                    allocations=store_records,
                )
            )

        highest_demand = max(metric_items, key=lambda x: x.total_forecasted_demand).scenario_name
        lowest_shortage = min(metric_items, key=lambda x: x.total_shortage).scenario_name
        highest_fulfillment = max(metric_items, key=lambda x: x.fulfillment_rate_percentage).scenario_name

        return CompareScenariosResponse(
            scenarios=metric_items,
            summary=ScenarioComparisonSummary(
                highest_demand_scenario=highest_demand,
                lowest_shortage_scenario=lowest_shortage,
                highest_fulfillment_scenario=highest_fulfillment,
            ),
            dataset_source="data/processed/sales.csv",
            is_real_data=True,
            unit="units",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario comparison failed: {exc}",
        )


@app.get(
    "/model-metrics",
    response_model=ModelMetricsResponse,
    summary="Get forecasting model accuracy metrics",
    description="Evaluates the moving average forecasting algorithm against a holdout window of historical sales, computing MAE, RMSE, WAPE, and Bias.",
)
def get_model_metrics(
    eval_window_days: int = Query(default=14, ge=7, le=60, description="Holdout evaluation window in days"),
) -> ModelMetricsResponse:
    """Calculates empirical holdout accuracy metrics (MAE, RMSE, WAPE, Bias) on historical sales."""
    try:
        raw_df = load_demand_data()
        if raw_df.empty:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demand dataset is empty.",
            )

        max_dt = pd.to_datetime(raw_df["date"]).max()
        cutoff_dt = max_dt - pd.Timedelta(days=eval_window_days)

        train_df = raw_df[pd.to_datetime(raw_df["date"]) <= cutoff_dt]
        test_df = raw_df[pd.to_datetime(raw_df["date"]) > cutoff_dt]

        if train_df.empty or test_df.empty:
            unique_dates = sorted(raw_df["date"].unique())
            split_idx = int(len(unique_dates) * 0.8)
            split_date = unique_dates[split_idx]
            train_df = raw_df[raw_df["date"] <= split_date]
            test_df = raw_df[raw_df["date"] > split_date]
            eval_window_days = len(unique_dates) - split_idx

        fc_df = forecast_demand(df=train_df, horizon_days=eval_window_days)

        merged = pd.merge(
            test_df,
            fc_df,
            left_on=["store_id", "sku_id", "date"],
            right_on=["store_id", "sku_id", "forecast_date"],
            how="inner",
        )

        if merged.empty:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to align historical test actuals with forecast dates.",
            )

        y_true = merged["units_sold"].values
        y_pred = merged["predicted_units"].values
        overall_dict = calculate_forecast_metrics(y_true, y_pred)
        acc_pct = max(0.0, round((1.0 - overall_dict["wape"]) * 100.0, 2))

        overall_metrics = OverallModelMetrics(
            mae=overall_dict["mae"],
            rmse=overall_dict["rmse"],
            wape=overall_dict["wape"],
            bias=overall_dict["bias"],
            accuracy_percentage=acc_pct,
        )

        sku_metrics: List[SkuModelMetric] = []
        for sku_id, group in merged.groupby("sku_id"):
            sku_str = str(sku_id)
            sku_res = calculate_forecast_metrics(group["units_sold"].values, group["predicted_units"].values)
            sku_metrics.append(
                SkuModelMetric(
                    sku_id=sku_str,
                    category=SKU_CATEGORY_MAP.get(sku_str, "General"),
                    mae=sku_res["mae"],
                    rmse=sku_res["rmse"],
                    wape=sku_res["wape"],
                    bias=sku_res["bias"],
                )
            )

        sku_metrics.sort(key=lambda x: x.sku_id)

        return ModelMetricsResponse(
            model_name="7-Day Moving Average with DOW Seasonality",
            algorithm="Moving Average + Multiplicative Day-of-Week Seasonality",
            dataset_source="data/processed/sales.csv (Retail Store POS Transactions)",
            is_real_data=True,
            evaluation_window_days=eval_window_days,
            evaluated_records=int(len(merged)),
            overall_metrics=overall_metrics,
            sku_metrics=sku_metrics,
            unit="units",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model evaluation failed: {exc}",
        )


@app.get("/forecast/bounds", response_model=List[ForecastItemWithBounds])
def get_forecast_with_bounds(
    horizon_days: int = Query(default=7, ge=1, le=365),
    is_holiday_week: bool = Query(default=False),
    promotion_store: Optional[str] = Query(default=None),
    promotion_multiplier: Optional[float] = Query(default=None),
    confidence_level: float = Query(default=0.90, ge=0.50, le=0.99),
) -> List[ForecastItemWithBounds]:
    """Generates demand forecasts augmented with empirical confidence bounds."""
    promo_boost = None
    if promotion_store is not None or promotion_multiplier is not None:
        if promotion_store is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="promotion_store must be provided when promotion_multiplier is specified.",
            )
        if promotion_multiplier is None:
            promotion_multiplier = 1.30
        if promotion_multiplier < 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"promotion_multiplier must be >= 1.0, got {promotion_multiplier}",
            )
        promo_boost = {promotion_store: float(promotion_multiplier)}

    try:
        raw_df = load_demand_data()
        fc_df = forecast_demand_with_bounds(
            df=raw_df,
            horizon_days=horizon_days,
            promo_boost=promo_boost,
            is_holiday_week=is_holiday_week,
            confidence_level=confidence_level,
        )
        return [ForecastItemWithBounds(**r) for r in fc_df.to_dict(orient="records")]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting with bounds failed: {exc}",
        )


@app.post("/allocate/sku", response_model=SkuAllocationResponse)
def post_allocate_sku(payload: SkuAllocationRequest) -> SkuAllocationResponse:
    """Performs multi-item constrained allocation at the store-SKU grain."""
    if payload.total_available_units is not None and payload.total_available_units < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="total_available_units must be non-negative.",
        )
    if payload.method not in ["proportional", "lp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown method '{payload.method}'. Supported: ['proportional', 'lp'].",
        )

    try:
        raw_df = load_demand_data()
        fc_df = forecast_demand(
            df=raw_df,
            horizon_days=payload.horizon_days,
            promo_boost=payload.promo_boost,
            is_holiday_week=payload.is_holiday_week,
        )

        sku_alloc_df = allocate_sku_inventory(
            forecast_df=fc_df,
            inventory_by_sku=payload.inventory_by_sku,
            total_available_units=payload.total_available_units,
            store_priorities=payload.store_priorities,
            sku_priorities=payload.sku_priorities,
            allocation_method=payload.method,
        )

        # Build overall summary
        tot_d = float(sku_alloc_df["forecasted_demand"].sum()) if not sku_alloc_df.empty else 0.0
        tot_a = float(sku_alloc_df["allocated_units"].sum()) if not sku_alloc_df.empty else 0.0
        tot_s = float(sku_alloc_df["shortage"].sum()) if not sku_alloc_df.empty else 0.0
        tot_e = float(sku_alloc_df["excess"].sum()) if not sku_alloc_df.empty else 0.0
        avail = float(payload.total_available_units or tot_a)
        rem = max(0.0, avail - tot_a)

        summary = AllocationSummary(
            total_forecasted_demand=tot_d,
            total_available_units=avail,
            total_allocated_units=tot_a,
            total_shortage=tot_s,
            total_excess=tot_e,
            remaining_inventory=rem,
        )

        records = [SkuAllocationItem(**r) for r in sku_alloc_df.to_dict(orient="records")]
        return SkuAllocationResponse(
            status="success",
            method=payload.method,
            allocations=records,
            summary=summary,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SKU allocation failed: {exc}",
        )


@app.post("/safety-stock", response_model=SafetyStockResponse)
def post_safety_stock(payload: SafetyStockRequest) -> SafetyStockResponse:
    """Calculates safety stock, reorder points, and replenishment urgency."""
    try:
        raw_df = load_demand_data()
        rec_df = calculate_safety_stock_and_reorder(
            historical_df=raw_df,
            current_inventory=payload.current_inventory,
            lead_time_days=payload.lead_time_days,
            target_service_level=payload.target_service_level,
            min_order_qty=payload.min_order_qty,
            pack_size=payload.pack_size,
        )
        items = [SafetyStockItem(**r) for r in rec_df.to_dict(orient="records")]
        return SafetyStockResponse(recommendations=items)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety stock calculation failed: {exc}",
        )


@app.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality() -> DataQualityResponse:
    """Returns dataset health metrics, grid completeness, and validation diagnostics."""
    try:
        report = get_data_quality_report()
        return DataQualityResponse(**report)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data quality audit failed: {exc}",
        )


@app.post("/reports/export")
def post_export_report(payload: AllocationRequest) -> Response:
    """Generates an 8-worksheet Excel workbook containing end-to-end allocation results."""
    try:
        raw_df = load_demand_data()
        fc_df = forecast_demand(
            df=raw_df,
            horizon_days=payload.horizon_days,
            promo_boost=payload.promo_boost,
            is_holiday_week=payload.is_holiday_week,
        )
        if payload.method == "lp":
            alloc_df = allocate_inventory_lp(fc_df, total_available_units=payload.total_available_units)
        else:
            alloc_df = allocate_inventory(fc_df, total_available_units=payload.total_available_units)

        sku_alloc_df = allocate_sku_inventory(fc_df, total_available_units=payload.total_available_units, allocation_method=payload.method)
        summary = alloc_df.attrs.get("summary", get_allocation_summary(alloc_df, payload.total_available_units))

        excel_bytes = generate_excel_report(
            forecast_df=fc_df,
            allocation_df=alloc_df,
            sku_allocation_df=sku_alloc_df,
            summary_dict=summary,
            scenario_assumptions={
                "Available Inventory": payload.total_available_units,
                "Allocation Method": payload.method,
                "Horizon (Days)": payload.horizon_days,
                "Holiday Uplift": payload.is_holiday_week,
                "Promotions": str(payload.promo_boost or "None"),
            },
        )

        headers = {
            "Content-Disposition": 'attachment; filename="inventory_allocation_report.xlsx"'
        }
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report export failed: {exc}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
