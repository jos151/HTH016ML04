"""
Data schemas and domain models for demand forecasting, inventory allocation, and simulation API.
"""

from typing import Any, Dict, List, Literal, Optional
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


class ForecastItemWithBounds(ForecastItem):
    """Forecast item augmented with empirical uncertainty bounds."""
    lower_confidence_bound: float = Field(default=0.0, description="Lower empirical confidence bound")
    upper_confidence_bound: float = Field(default=0.0, description="Upper empirical confidence bound")
    confidence_level: float = Field(default=0.90, description="Nominal confidence level")
    uncertainty_risk: str = Field(default="Low", description="Uncertainty risk classification: Low, Medium, High")


class SkuAllocationItem(BaseModel):
    """Store-SKU level allocation outcome."""
    warehouse_id: str
    allocation_date: str
    store_id: str
    sku_id: str
    forecasted_demand: int
    available_sku_inventory: int
    allocated_units: int
    shortage: int
    excess: int
    fulfillment_percentage: float
    allocation_method: str
    priority_weight: float


class SkuAllocationRequest(BaseModel):
    """Request payload for store-SKU granular allocation."""
    total_available_units: Optional[float] = Field(default=1000.0, ge=0.0)
    inventory_by_sku: Optional[Dict[str, float]] = Field(default=None)
    store_priorities: Optional[Dict[str, float]] = Field(default=None)
    sku_priorities: Optional[Dict[str, float]] = Field(default=None)
    method: Literal["proportional", "lp"] = Field(default="proportional")
    horizon_days: int = Field(default=7, ge=1, le=365)
    is_holiday_week: bool = Field(default=False)
    promo_boost: Optional[Dict[str, float]] = Field(default=None)


class SkuAllocationResponse(BaseModel):
    """Response payload for store-SKU granular allocation."""
    status: str
    method: str
    allocations: List[SkuAllocationItem]
    summary: AllocationSummary


class SafetyStockItem(BaseModel):
    """Safety stock and replenishment recommendation per SKU."""
    sku_id: str
    avg_daily_demand: float
    demand_std_dev: float
    lead_time_days: int
    lead_time_demand: float
    safety_stock: int
    reorder_point: int
    current_inventory: int
    suggested_order_qty: int
    days_of_cover: float
    urgency: str
    recommended_action: str
    service_level_target: float
    z_score: float


class SafetyStockRequest(BaseModel):
    """Request for safety stock calculation."""
    lead_time_days: int = Field(default=7, ge=1, le=60)
    target_service_level: float = Field(default=0.95, ge=0.50, le=0.999)
    min_order_qty: int = Field(default=10, ge=1)
    pack_size: int = Field(default=5, ge=1)
    current_inventory: Optional[Dict[str, float]] = Field(default=None)


class SafetyStockResponse(BaseModel):
    """Response containing replenishment recommendations."""
    recommendations: List[SafetyStockItem]


class DataQualityResponse(BaseModel):
    """Audit metrics for sales dataset health."""
    status: str
    dataset_source: str
    is_real_data: bool
    row_count: int
    date_range: Dict[str, Any]
    store_count: int
    sku_count: int
    missing_values: Dict[str, int]
    duplicate_count: int
    negative_sales_count: int
    zero_sales_count: int
    zero_sales_percentage: float
    missing_combination_count: int
    warnings: List[str]
    stores: List[str]
    skus: List[str]


class MetadataResponse(BaseModel):
    """Dataset entity catalog metadata."""
    stores: List[str]
    skus: List[str]
    categories: List[str]
    min_date: str
    max_date: str
    total_rows: int
