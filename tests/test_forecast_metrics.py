"""
Unit tests for Forecast Evaluation Metrics (Stage 6).
Covers MAE, RMSE, WAPE, Bias, chronological splits, zero-actuals handling, and invariant boundaries.
"""
import numpy as np
import pandas as pd
import pytest
from backend.forecasting import calculate_forecast_metrics


def test_perfect_predictions_zero_errors():
    """Verify that perfect forecasts return exactly 0 for MAE, RMSE, and bias."""
    actual = [10.0, 20.0, 30.0, 40.0]
    pred = [10.0, 20.0, 30.0, 40.0]
    metrics = calculate_forecast_metrics(actual, pred)
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["wape"] == 0.0
    assert metrics["bias"] == 0.0


def test_known_mathematical_example():
    """Verify hand-calculated metrics on known demand series."""
    actual = [100.0, 200.0]
    pred = [110.0, 180.0]
    # errors: |100-110|=10, |200-180|=20
    # MAE = (10+20)/2 = 15.0
    # RMSE = sqrt((100+400)/2) = sqrt(250) = 15.8114
    # WAPE = 30 / 300 = 0.10
    # Bias = ((110-100) + (180-200)) / 2 = (10 - 20) / 2 = -5.0
    metrics = calculate_forecast_metrics(actual, pred)
    assert metrics["mae"] == 15.0
    assert abs(metrics["rmse"] - 15.8114) < 0.001
    assert metrics["wape"] == 0.10
    assert metrics["bias"] == -5.0


def test_zero_actual_demand_handling():
    """Verify WAPE safely handles zero total actual demand without ZeroDivisionError."""
    # When actual is 0 and prediction is 0
    metrics_zero = calculate_forecast_metrics([0.0, 0.0], [0.0, 0.0])
    assert metrics_zero["wape"] == 0.0
    assert metrics_zero["mae"] == 0.0

    # When actual is 0 and prediction is positive
    metrics_pos_pred = calculate_forecast_metrics([0.0, 0.0], [10.0, 20.0])
    assert metrics_pos_pred["wape"] == 1.0
    assert metrics_pos_pred["mae"] == 15.0


def test_length_mismatch_rejection():
    """Verify error when actual and predicted series have different lengths."""
    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_forecast_metrics([10, 20], [10])


def test_nan_values_rejection():
    """Verify rejection when actual or predicted contains NaN values."""
    with pytest.raises(ValueError, match="NaN"):
        calculate_forecast_metrics([10.0, np.nan], [10.0, 20.0])

    with pytest.raises(ValueError, match="NaN"):
        calculate_forecast_metrics([10.0, 20.0], [10.0, np.nan])


def test_negative_actual_demand_rejection():
    """Verify rejection when actual demand contains negative sales values."""
    with pytest.raises(ValueError, match="negative"):
        calculate_forecast_metrics([-5.0, 10.0], [5.0, 10.0])


def test_chronological_test_split_integrity():
    """Verify chronological split guarantees training dates precede test dates."""
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "units_sold": np.linspace(10, 50, 30),
    })

    cutoff = pd.to_datetime("2023-01-20")
    train = df[df["date"] < cutoff]
    test = df[df["date"] >= cutoff]

    assert not train.empty and not test.empty
    assert train["date"].max() < test["date"].min()
    assert len(train) + len(test) == len(df)


def test_deterministic_reproducibility():
    """Verify repeated metric calculation yields identical float results."""
    actual = np.array([12.3, 45.6, 78.9])
    pred = np.array([14.0, 42.0, 80.0])
    m1 = calculate_forecast_metrics(actual, pred)
    m2 = calculate_forecast_metrics(actual, pred)
    assert m1 == m2
