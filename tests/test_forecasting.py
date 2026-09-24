"""
Unit and integration tests for backend/forecasting.py covering horizon handling,
seasonality, multipliers, cold-start fallback, evaluation metrics, and immutability.
"""

from datetime import datetime
import numpy as np
import pandas as pd
import pytest
from backend.forecasting import forecast_demand, calculate_forecast_metrics


@pytest.fixture
def sample_history():
    """Provides 14 days of deterministic history for 2 stores and 2 SKUs."""
    dates = pd.date_range("2023-01-01", periods=14, freq="D")
    records = []
    val = 10
    for d in dates:
        for s in ["STORE_A", "STORE_B"]:
            for k in ["SKU_1", "SKU_2"]:
                records.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "store_id": s,
                    "sku_id": k,
                    "units_sold": val,
                })
                val = (val + 2) % 30
    return pd.DataFrame(records)


def test_correct_output_columns(sample_history):
    """1. Tests that forecast_demand returns the required output columns."""
    df_out = forecast_demand(sample_history, horizon_days=7)
    expected_cols = [
        "store_id",
        "sku_id",
        "forecast_date",
        "baseline_units",
        "promo_multiplier",
        "holiday_multiplier",
        "predicted_units",
    ]
    assert list(df_out.columns) == expected_cols


def test_correct_forecast_horizon(sample_history):
    """2. Tests that default horizon generates exactly 7 forecast dates per group."""
    df_out = forecast_demand(sample_history, horizon_days=7)
    # 2 stores * 2 SKUs * 7 days = 28 rows
    assert len(df_out) == 28
    assert df_out["forecast_date"].nunique() == 7


def test_multiple_horizon_values(sample_history):
    """3. Tests forecasts with different horizon values (e.g., 3, 14, 30 days)."""
    for h in [3, 14, 30]:
        df_out = forecast_demand(sample_history, horizon_days=h)
        assert df_out["forecast_date"].nunique() == h
        assert len(df_out) == 2 * 2 * h


def test_non_negative_predictions(sample_history):
    """4. Tests that all predictions and baselines are strictly non-negative."""
    df_out = forecast_demand(sample_history, horizon_days=7)
    assert (df_out["predicted_units"] >= 0.0).all()
    assert (df_out["baseline_units"] >= 0.0).all()


def test_no_nan_values(sample_history):
    """5. Tests that output contains no NaN, null, or infinite values."""
    df_out = forecast_demand(sample_history, horizon_days=7)
    assert df_out.isnull().sum().sum() == 0
    assert not np.isinf(df_out["predicted_units"]).any()


def test_promotion_multiplier(sample_history):
    """6. Tests that promo_boost applies only to the designated store."""
    promo_boost = {"STORE_A": 1.30}
    df_out = forecast_demand(sample_history, horizon_days=7, promo_boost=promo_boost)

    store_a = df_out[df_out["store_id"] == "STORE_A"]
    store_b = df_out[df_out["store_id"] == "STORE_B"]

    assert (store_a["promo_multiplier"] == 1.30).all()
    assert (store_b["promo_multiplier"] == 1.00).all()


def test_holiday_multiplier(sample_history):
    """7. Tests that is_holiday_week applies +15% uplift (1.15 multiplier)."""
    df_base = forecast_demand(sample_history, horizon_days=7, is_holiday_week=False)
    df_hol = forecast_demand(sample_history, horizon_days=7, is_holiday_week=True)

    assert (df_base["holiday_multiplier"] == 1.00).all()
    assert (df_hol["holiday_multiplier"] == 1.15).all()

    # Predicted units should scale up by 1.15
    ratio = df_hol["predicted_units"].sum() / df_base["predicted_units"].sum()
    assert abs(ratio - 1.15) < 0.01


def test_combined_promotion_and_holiday(sample_history):
    """8. Tests multiplicative combination of promotion and holiday."""
    promo_boost = {"STORE_A": 1.30}
    df_out = forecast_demand(
        sample_history,
        horizon_days=7,
        promo_boost=promo_boost,
        is_holiday_week=True,
    )
    store_a = df_out[df_out["store_id"] == "STORE_A"]
    # 1.30 * 1.15 = 1.495 multiplier on baseline
    for row in store_a.itertuples():
        expected_pred = round(row.baseline_units * 1.30 * 1.15, 2)
        assert abs(row.predicted_units - expected_pred) <= 0.02


def test_unaffected_stores_remain_unchanged(sample_history):
    """9. Tests that unboosted stores have identical predictions whether another store is boosted or not."""
    df_no_boost = forecast_demand(sample_history, horizon_days=7, promo_boost=None)
    df_with_boost = forecast_demand(sample_history, horizon_days=7, promo_boost={"STORE_A": 1.30})

    b_no_boost = df_no_boost[df_no_boost["store_id"] == "STORE_B"]["predicted_units"].reset_index(drop=True)
    b_with_boost = df_with_boost[df_with_boost["store_id"] == "STORE_B"]["predicted_units"].reset_index(drop=True)

    pd.testing.assert_series_equal(b_no_boost, b_with_boost)


def test_short_history_fallback():
    """10. Tests cold-start fallback when a store-SKU group has fewer than 7 observations."""
    short_df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "store_id": ["STORE_X", "STORE_X", "STORE_X"],
        "sku_id": ["SKU_NEW", "SKU_NEW", "SKU_NEW"],
        "units_sold": [10.0, 20.0, 30.0],
    })
    df_out = forecast_demand(short_df, horizon_days=5)
    assert len(df_out) == 5
    # Mean of 10, 20, 30 is 20.0
    assert (df_out["baseline_units"] == 20.0).all()
    assert (df_out["predicted_units"] == 20.0).all()


def test_zero_demand_history():
    """11. Tests forecasting for an item with all zero demand history."""
    zero_df = pd.DataFrame({
        "date": [f"2023-01-{i:02d}" for i in range(1, 15)],
        "store_id": ["STORE_Z"] * 14,
        "sku_id": ["SKU_ZERO"] * 14,
        "units_sold": [0.0] * 14,
    })
    df_out = forecast_demand(zero_df, horizon_days=7)
    assert len(df_out) == 7
    assert (df_out["predicted_units"] == 0.0).all()


def test_invalid_horizon(sample_history):
    """12. Tests that non-positive or excessive horizon raises ValueError."""
    with pytest.raises(ValueError, match="horizon_days must be a positive integer"):
        forecast_demand(sample_history, horizon_days=0)

    with pytest.raises(ValueError, match="horizon_days must be a positive integer"):
        forecast_demand(sample_history, horizon_days=-5)

    with pytest.raises(ValueError, match="horizon_days must be a positive integer"):
        forecast_demand(sample_history, horizon_days=500)


def test_deterministic_output(sample_history):
    """13. Tests that repeated calls produce strictly identical predictions."""
    df_1 = forecast_demand(sample_history, horizon_days=7, promo_boost={"STORE_A": 1.25})
    df_2 = forecast_demand(sample_history, horizon_days=7, promo_boost={"STORE_A": 1.25})
    pd.testing.assert_frame_equal(df_1, df_2)


def test_input_dataframe_immutability(sample_history):
    """14. Tests that input DataFrame is not mutated or modified."""
    copy_before = sample_history.copy(deep=True)
    _ = forecast_demand(sample_history, horizon_days=7, promo_boost={"STORE_A": 1.30})
    pd.testing.assert_frame_equal(sample_history, copy_before)


def test_calculate_forecast_metrics():
    """15. Tests evaluation metric calculations (MAE, RMSE, WAPE)."""
    actual = [100.0, 200.0, 300.0]
    pred = [110.0, 190.0, 300.0]
    metrics = calculate_forecast_metrics(actual, pred)

    assert "mae" in metrics and "rmse" in metrics and "wape" in metrics
    # Absolute errors: 10, 10, 0 -> MAE = 20 / 3 = 6.6667
    assert abs(metrics["mae"] - 6.6667) < 0.001
    # Squared errors: 100, 100, 0 -> RMSE = sqrt(200/3) = 8.1650
    assert abs(metrics["rmse"] - 8.1650) < 0.001
    # WAPE = 20 / 600 = 0.0333
    assert abs(metrics["wape"] - 0.0333) < 0.001
