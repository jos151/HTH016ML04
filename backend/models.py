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


class ErrorResponse(BaseModel):
    """Standardized error response payload for mobile clients."""
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable explanation of error")
    field: Optional[str] = Field(default=None, description="Specific request payload field that failed validation")
    details: Optional[Any] = Field(default=None, description="Detailed validation breakdown or error context")
    request_id: Optional[str] = Field(default=None, description="Unique correlation identifier for request tracing")
    detail: Optional[str] = Field(default=None, description="FastAPI standard detail property for backwards compatibility")


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
    inventory_by_sku: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional inventory breakdown per SKU",
    )
    store_priorities: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional priority weights per store (>= 0.1)",
    )
    sku_priorities: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional priority weights per SKU (>= 0.1)",
    )
    shortage_cost: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        description="Penalty weight per unit of unsatisfied demand (LP method)",
    )
    overstock_cost: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        description="Holding cost per unit of inventory allocated beyond demand (LP method)",
    )
    include_sku_breakdown: bool = Field(
        default=False,
        description="Whether to include store-SKU granular allocation items in response",
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
    sku_allocations: Optional[List[Any]] = Field(default=None, description="Optional store-SKU breakdown")
    method: str = Field(default="proportional", description="Allocation algorithm used")
    unit: str = Field(default="units", description="Unit of measurement")
    dataset_source: str = Field(default="data/processed/sales.csv", description="Source data path")
    is_real_data: bool = Field(default=True, description="Whether data is empirical")


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


# =====================================================================
# Mobile & Extended API Contract Schemas
# =====================================================================

class CategoryItem(BaseModel):
    """Detailed category catalog item."""
    category_id: str = Field(..., description="Unique category identifier (e.g. CAT_01)")
    name: str = Field(..., description="Human-readable category name")
    sku_count: int = Field(..., description="Number of SKUs assigned to this category")
    skus: List[str] = Field(..., description="List of SKU identifiers")


class CategoriesResponse(BaseModel):
    """Catalog of product categories."""
    total: int = Field(..., description="Total category count")
    categories: List[CategoryItem] = Field(..., description="List of category records")


class HistoryRecordItem(BaseModel):
    """Individual historical POS demand record."""
    date: str = Field(..., description="Observation date (ISO 8601: YYYY-MM-DD)")
    store_id: str = Field(..., description="Store identifier")
    sku_id: str = Field(..., description="SKU identifier")
    category: str = Field(..., description="Product category")
    units_sold: float = Field(..., description="Quantity of units sold")
    day_of_week: str = Field(..., description="Day of week name")
    is_weekend: bool = Field(..., description="True if Saturday or Sunday")


class HistorySummary(BaseModel):
    """System-wide summary metrics for filtered historical records."""
    total_records: int = Field(..., description="Total matching historical rows")
    total_units_sold: float = Field(..., description="Total units sold across all matching records")
    average_units_per_record: float = Field(..., description="Average units sold per record")
    min_date: str = Field(..., description="Earliest observation date")
    max_date: str = Field(..., description="Latest observation date")
    distinct_stores: int = Field(..., description="Number of distinct stores")
    distinct_skus: int = Field(..., description="Number of distinct SKUs")


class HistoryResponse(BaseModel):
    """Paginated historical demand response."""
    items: List[HistoryRecordItem] = Field(..., description="Paginated historical records")
    total: int = Field(..., description="Total matching records across all pages")
    page: int = Field(..., description="Current 1-based page number")
    page_size: int = Field(..., description="Records per page")
    total_pages: int = Field(..., description="Total available pages")
    summary: HistorySummary = Field(..., description="Summary totals across all matching records")
    dataset_source: str = Field(default="data/processed/sales.csv", description="Origin of sales dataset")
    is_real_data: bool = Field(default=True, description="Whether dataset is empirical retail data")
    unit: str = Field(default="units", description="Unit of measurement")


class MobileForecastRequest(BaseModel):
    """Enhanced forecast request payload for mobile clients."""
    horizon_days: int = Field(default=7, ge=1, le=365, description="Forecast horizon in days")
    stores: Optional[List[str]] = Field(default=None, description="Optional store filter (null/empty means all)")
    skus: Optional[List[str]] = Field(default=None, description="Optional SKU filter (null/empty means all)")
    categories: Optional[List[str]] = Field(default=None, description="Optional category filter")
    promo_boost: Optional[Dict[str, float]] = Field(default=None, description="Store promotional multipliers (>= 1.0)")
    is_holiday_week: bool = Field(default=False, description="Apply holiday uplift (+15%)")
    start_date: Optional[str] = Field(default=None, description="Filter forecast start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="Filter forecast end date (YYYY-MM-DD)")
    confidence_level: Optional[float] = Field(default=0.90, ge=0.50, le=0.99, description="Confidence level for uncertainty bounds")

    @field_validator("promo_boost")
    @classmethod
    def validate_promo_boost(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            for store, mult in v.items():
                if mult < 1.0:
                    raise ValueError(f"Promotion multiplier for store '{store}' must be at least 1.0, got {mult}")
        return v


class MobileForecastItem(BaseModel):
    """Forecast item with uncertainty bounds and category classification."""
    store_id: str = Field(..., description="Store identifier")
    sku_id: str = Field(..., description="SKU identifier")
    category: str = Field(..., description="Product category")
    forecast_date: str = Field(..., description="Forecast date (ISO 8601: YYYY-MM-DD)")
    baseline_units: float = Field(..., description="Baseline demand before adjustments")
    promo_multiplier: float = Field(..., description="Promotional boost multiplier applied")
    holiday_multiplier: float = Field(..., description="Holiday boost multiplier applied")
    predicted_units: float = Field(..., description="Final predicted demand units")
    lower_confidence_bound: float = Field(..., description="Lower empirical confidence bound")
    upper_confidence_bound: float = Field(..., description="Upper empirical confidence bound")
    confidence_level: float = Field(..., description="Confidence level")
    uncertainty_risk: str = Field(..., description="Risk tier: Low, Medium, High")


class ForecastSummary(BaseModel):
    """Summary metrics for the forecast output."""
    total_baseline_units: float = Field(..., description="Sum of baseline units across forecast")
    total_predicted_units: float = Field(..., description="Sum of predicted units across forecast")
    average_daily_units: float = Field(..., description="Average predicted units per day")
    distinct_stores: int = Field(..., description="Distinct stores in forecast")
    distinct_skus: int = Field(..., description="Distinct SKUs in forecast")
    forecast_start_date: str = Field(..., description="Earliest forecast date")
    forecast_end_date: str = Field(..., description="Latest forecast date")


class MobileForecastResponse(BaseModel):
    """Comprehensive mobile forecast response."""
    forecast_items: List[MobileForecastItem] = Field(..., description="Item-level demand forecasts")
    summary: ForecastSummary = Field(..., description="Forecast summary totals")
    horizon_days: int = Field(..., description="Forecast horizon in days")
    is_holiday_week: bool = Field(..., description="Whether holiday uplift was applied")
    model_name: str = Field(default="7-Day Moving Average with DOW Seasonality", description="Active forecasting model")
    algorithm: str = Field(default="Moving Average + Multiplicative Day-of-Week Seasonality", description="Underlying algorithm")
    dataset_source: str = Field(default="data/processed/sales.csv (Retail Store POS Transactions)", description="Source dataset")
    is_real_data: bool = Field(default=True, description="Whether data is empirical")
    unit: str = Field(default="units", description="Unit of measurement")
    generated_at: str = Field(..., description="ISO 8601 timestamp of forecast generation")


class ScenarioInput(BaseModel):
    """Input parameters for a single scenario comparison trial."""
    scenario_name: str = Field(..., description="Descriptive identifier for this scenario")
    horizon_days: int = Field(default=7, ge=1, le=365, description="Forecast horizon in days")
    total_available_units: float = Field(default=1000.0, ge=0.0, description="Available supply for this scenario")
    method: Literal["proportional", "lp"] = Field(default="proportional", description="Allocation method")
    promo_boost: Optional[Dict[str, float]] = Field(default=None, description="Store promotion multipliers")
    is_holiday_week: bool = Field(default=False, description="Apply holiday uplift")


class CompareScenariosRequest(BaseModel):
    """Request payload to compare multiple what-if scenarios side-by-side."""
    scenarios: List[ScenarioInput] = Field(..., min_length=2, max_length=10, description="List of 2 to 10 scenarios to compare")


class ScenarioMetricItem(BaseModel):
    """Key outcome indicators for a single scenario."""
    scenario_name: str = Field(..., description="Scenario identifier")
    horizon_days: int = Field(..., description="Forecast horizon")
    total_available_units: float = Field(..., description="Available inventory constraint")
    total_forecasted_demand: float = Field(..., description="Total forecasted demand across stores")
    total_allocated_units: float = Field(..., description="Total units allocated")
    total_shortage: float = Field(..., description="Total unsatisfied demand")
    total_excess: float = Field(..., description="Total excess inventory")
    fulfillment_rate_percentage: float = Field(..., description="Percentage of demand fulfilled")
    shortage_percentage: float = Field(..., description="Shortage as percentage of demand")
    allocations: List[StoreAllocationResult] = Field(..., description="Store-level breakdown")


class ScenarioComparisonSummary(BaseModel):
    """High-level summary comparing all submitted scenarios."""
    highest_demand_scenario: str = Field(..., description="Scenario with greatest total demand")
    lowest_shortage_scenario: str = Field(..., description="Scenario with minimal total shortage")
    highest_fulfillment_scenario: str = Field(..., description="Scenario with highest fulfillment percentage")


class CompareScenariosResponse(BaseModel):
    """Comparison evaluation across multiple scenarios."""
    scenarios: List[ScenarioMetricItem] = Field(..., description="Evaluation outcome for each scenario")
    summary: ScenarioComparisonSummary = Field(..., description="High-level comparison conclusions")
    dataset_source: str = Field(default="data/processed/sales.csv", description="Source sales dataset")
    is_real_data: bool = Field(default=True, description="Whether data is empirical")
    unit: str = Field(default="units", description="Measurement unit")


class SkuModelMetric(BaseModel):
    """Forecast performance metrics for an individual SKU."""
    sku_id: str = Field(..., description="SKU identifier")
    category: str = Field(..., description="Product category")
    mae: float = Field(..., description="Mean Absolute Error (units)")
    rmse: float = Field(..., description="Root Mean Squared Error (units)")
    wape: float = Field(..., description="Weighted Absolute Percentage Error (0.0 to 1.0)")
    bias: float = Field(..., description="Mean Forecast Bias (positive=overforecast, negative=underforecast)")


class OverallModelMetrics(BaseModel):
    """System-wide forecast accuracy indicators."""
    mae: float = Field(..., description="Mean Absolute Error across all store-SKU combinations")
    rmse: float = Field(..., description="Root Mean Squared Error across all store-SKU combinations")
    wape: float = Field(..., description="System-wide Weighted Absolute Percentage Error")
    bias: float = Field(..., description="System-wide Forecast Bias")
    accuracy_percentage: float = Field(..., description="Estimated forecast accuracy percentage (1 - WAPE) * 100")


class ModelMetricsResponse(BaseModel):
    """Empirical accuracy metrics evaluating the forecasting model against historical holdout."""
    model_name: str = Field(default="7-Day Moving Average with DOW Seasonality", description="Active forecast model")
    algorithm: str = Field(default="Moving Average + Multiplicative Day-of-Week Seasonality", description="Forecasting algorithm")
    dataset_source: str = Field(default="data/processed/sales.csv (Retail Store POS Transactions)", description="Source dataset")
    is_real_data: bool = Field(default=True, description="Empirical vs synthetic indicator")
    evaluation_window_days: int = Field(..., description="Length of holdout evaluation period in days")
    evaluated_records: int = Field(..., description="Number of historical store-SKU daily records evaluated")
    overall_metrics: OverallModelMetrics = Field(..., description="Aggregate system metrics")
    sku_metrics: List[SkuModelMetric] = Field(..., description="Per-SKU performance breakdown")
    unit: str = Field(default="units", description="Unit of demand measurement")
