"""
FastAPI application entrypoint and API router definitions for retail demand
forecasting, inventory allocation, and scenario simulation.
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.data_loader import load_demand_data, STORE_IDS
from backend.forecasting import forecast_demand
from backend.allocation import allocate_inventory, allocate_inventory_lp, get_allocation_summary
from backend.models import (
    HealthResponse,
    ForecastItem,
    AllocationRequest,
    AllocationResponse,
    SimulationRequest,
    SimulationResponse,
    ScenarioResult,
    StoreAllocationResult,
    AllocationSummary,
)

app = FastAPI(
    title="Inventory-Constrained Demand Forecasting and Allocation API",
    description="REST API for store-SKU demand forecasting, proportional inventory allocation, and scenario simulation.",
    version="1.0.0",
)

# Permissive CORS middleware for local hackathon and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            )
        else:
            allocation_df = allocate_inventory(
                forecast_df=forecast_df,
                total_available_units=payload.total_available_units,
            )

        summary_dict = allocation_df.attrs.get(
            "summary",
            get_allocation_summary(allocation_df, payload.total_available_units),
        )

        alloc_records = allocation_df.to_dict(orient="records")
        return AllocationResponse(
            allocations=[StoreAllocationResult(**r) for r in alloc_records],
            summary=AllocationSummary(**summary_dict),
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
