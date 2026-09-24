import os
from pathlib import Path
import pytest
import pandas as pd

# Ensure local test client requests bypass any system proxy
os.environ["NO_PROXY"] = "localhost,127.0.0.1"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns absolute path to project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_demand_df(project_root: Path) -> pd.DataFrame:
    """Provides a deterministic sample demand DataFrame for testing."""
    fixture_path = project_root / "data" / "test_fixtures" / "sample_demand_fixture.csv"
    if fixture_path.exists():
        return pd.read_csv(fixture_path)
    # Fallback in-memory DataFrame
    dates = pd.date_range("2023-01-01", periods=14, freq="D")
    records = []
    for d in dates:
        for s in ["STORE_1", "STORE_2"]:
            for k in ["SKU_01", "SKU_02"]:
                records.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "store_id": s,
                    "sku_id": k,
                    "units_sold": 10.0,
                })
    return pd.DataFrame(records)
