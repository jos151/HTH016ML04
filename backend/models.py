"""
Data schemas and domain models for demand forecasting, inventory allocation, and simulation API.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """System health check and dataset inventory summary response."""
    status: str = Field(..., description="Service status (e.g. 'ok')")
    data_loaded: bool = Field(..., description="Whether retail demand data is available")
    row_count: int = Field(..., description="Total rows in sales dataset")
    store_count: int = Field(..., description="Count of distinct stores")
    sku_count: int = Field(..., description="Count of distinct SKUs")
    minimum_date: str = Field(..., description="Earliest observation date")
    maximum_date: str = Field(..., description="Latest observation date")


class ForecastItem(BaseModel):
    """Schema for individual forecast record."""
    store_id: str
    sku_id: str
    forecast_date: str
    baseline_units: float
    promo_multiplier: float
    holiday_multiplier: float
    predicted_units: float


class AllocationRequest(BaseModel):
    """Request payload for inventory allocation."""
    total_available_units: float = Field(..., description="Total inventory units available to allocate")
    method: Literal["proportional", "lp"] = Field(
        default="proportional",
        description="Allocation strategy: 'proportional' or 'lp' (linear programming)",
    )
    horizon_days: int = Field(default=7, ge=1, le=365, description="Forecast horizon in days")
    is_holiday_week: bool = Field(default=False, description="Apply +15% holiday uplift")
    promo_boost: Optional[Dict[str, float]] = Field(
        default=None,
        description="Store promotion multipliers mapping (e.g. {'STORE_1': 1.30})",
    )

    @field_validator("total_available_units")
    @classmethod
    def validate_non_negative_inventory(cls, v: float) -> float:
        if v < 0:
            raise ValueError("total_available_units must be non-negative (>= 0)")
        return v

    @field_validator("promo_boost")
    @classmethod
    def validate_promo_boost(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            for store, mult in v.items():
                if mult < 1.0:
                    raise ValueError(f"Promotion multiplier for store '{store}' must be at least 1.0, got {mult}")
        return v


class StoreAllocationResult(BaseModel):
    """Allocation outcome for an individual store."""
    store_id: str
    forecasted_demand: int
    allocated_units: int
    shortage: int
    excess: int


class AllocationSummary(BaseModel):
    """System-wide summary metrics for an allocation cycle."""
    total_forecasted_demand: float
    total_available_units: float
    total_allocated_units: float
    total_shortage: float
    total_excess: float
    remaining_inventory: float


class AllocationResponse(BaseModel):
    """Full allocation response containing store allocations and summary metrics."""
    allocations: List[StoreAllocationResult]
    summary: AllocationSummary


class SimulationRequest(BaseModel):
    """Request payload for scenario simulation."""
    horizon_days: int = Field(default=7, ge=1, le=365, description="Number of days to forecast")
    total_available_units: Optional[float] = Field(
        default=1000.0,
        ge=0.0,
        description="Available inventory units for scenario comparison",
    )
    promo_boost: Optional[Dict[str, float]] = Field(
        default=None,
        description="Store promotion multipliers mapping (e.g. {'STORE_1': 1.30})",
    )
    is_holiday_week: bool = Field(default=False, description="Apply holiday uplift")

    @field_validator("promo_boost")
    @classmethod
    def validate_simulation_promo(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            for store, mult in v.items():
                if mult < 1.0:
                    raise ValueError(f"Promotion multiplier for store '{store}' must be at least 1.0, got {mult}")
        return v


class ScenarioResult(BaseModel):
    """Container for forecast and allocation results of a single scenario."""
    scenario_name: str
    total_demand: float
    total_allocated: float
    total_shortage: float
    allocations: List[StoreAllocationResult]
    forecast_preview: List[ForecastItem]


class SimulationResponse(BaseModel):
    """Comparison response containing baseline and adjusted scenarios."""
    baseline: ScenarioResult
    adjusted: ScenarioResult
    demand_lift_percentage: float
    shortage_change: float
