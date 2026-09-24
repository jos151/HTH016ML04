"""FastAPI application entrypoint and API router definitions."""

from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from backend.data_loader import load_demand_data
    from backend.forecasting import forecast_demand
    from backend.allocation import allocate_inventory, allocate_inventory_lp
except ImportError:
    from data_loader import load_demand_data
    from forecasting import forecast_demand
    from allocation import allocate_inventory, allocate_inventory_lp

app = FastAPI(
    title="Demand Forecasting & Inventory Allocation API",
    description="API for retail demand forecasting and inventory allocation optimization.",
    version="1.0.0",
)

# Permissive CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AllocationRequest(BaseModel):
    total_available_units: int = Field(..., description="Total inventory units available to allocate", ge=0)
    method: Literal["proportional", "lp"] = Field(
        default="proportional",
        description="Allocation strategy: 'proportional' or 'lp' (linear programming)",
    )


@app.get("/forecast")
def get_forecast(
    horizon_days: int = Query(default=7, ge=1, description="Number of days to forecast"),
    is_holiday_week: bool = Query(default=False, description="Apply +15% holiday uplift"),
):
    """Generates demand forecast for all stores and SKUs across horizon_days."""
    try:
        raw_df = load_demand_data()
        forecast_df = forecast_demand(
            df=raw_df,
            horizon_days=horizon_days,
            is_holiday_week=is_holiday_week,
        )
        return forecast_df.to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/allocate")
def post_allocate(payload: AllocationRequest):
    """Allocates inventory across stores using proportional or linear programming optimization."""
    try:
        raw_df = load_demand_data()
        forecast_df = forecast_demand(df=raw_df, horizon_days=7)

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

        return allocation_df.to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
