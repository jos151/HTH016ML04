"""
Configuration settings for demand forecasting and inventory allocation.
"""

from pathlib import Path
from pydantic import BaseModel, Field

# Base project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TEST_FIXTURES_DIR = DATA_DIR / "test_fixtures"
DEFAULT_SALES_PATH = DATA_DIR / "sales.csv"


class AppConfig(BaseModel):
    """Core application settings."""
    app_title: str = "Demand Forecasting & Inventory Allocation"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    default_horizon_days: int = 7
    holiday_uplift_multiplier: float = 1.15
    default_shortage_cost: float = 1.0
    default_overstock_cost: float = 0.3


config = AppConfig()
