"""
Demand forecasting models, baseline calculation, seasonality, cold-start handling,
and chronological evaluation metrics.
"""

from pathlib import Path
import sys
from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd


def calculate_forecast_metrics(
    actual: Union[pd.Series, np.ndarray, list],
    predicted: Union[pd.Series, np.ndarray, list],
) -> Dict[str, float]:
    """Calculates chronological forecast accuracy metrics: MAE, RMSE, and WAPE.

    Handles zero actual demand safely when computing WAPE.

    Parameters:
        actual: Ground truth demand values.
        predicted: Model predicted demand values.

    Returns:
        Dict[str, float]: Dictionary with 'mae', 'rmse', and 'wape' keys.
    """
    y_true = np.asarray(actual, dtype=float)
    y_pred = np.asarray(predicted, dtype=float)

    if len(y_true) == 0 or len(y_pred) == 0:
        return {"mae": 0.0, "rmse": 0.0, "wape": 0.0}

    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Length mismatch: actual has {len(y_true)} items, predicted has {len(y_pred)} items."
        )

    errors = np.abs(y_true - y_pred)
    mae = float(np.mean(errors))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    sum_actual = float(np.sum(y_true))
    if sum_actual > 0:
        wape = float(np.sum(errors) / sum_actual)
    else:
        # If total actual demand is 0, WAPE is 0.0 if predictions are also 0, else 1.0
        wape = 0.0 if np.sum(y_pred) == 0 else 1.0

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "wape": round(wape, 4),
    }


def forecast_demand(
    df: pd.DataFrame,
    horizon_days: int = 7,
    promo_boost: Optional[Dict[str, float]] = None,
    is_holiday_week: bool = False,
) -> pd.DataFrame:
    """Forecasts store-and-SKU level demand for horizon_days into the future.

    Features:
    1. Group records by store_id and sku_id.
    2. Seven-day moving average baseline.
    3. Day-of-week seasonality factors derived from historical observations.
    4. Hierarchical cold-start fallback when fewer than 7 observations exist:
       (a) group mean -> (b) SKU average -> (c) store average -> (d) global average -> (e) 0.0
    5. Store-specific promotional boost multiplier (promo_boost).
    6. Holiday uplift multiplier (1.15 when is_holiday_week is True).
    7. Multiplicative combination when both promotion and holiday are enabled.
    8. Non-negative predictions and NaN/inf prevention.
    9. Deterministic rounding to 2 decimal places.

    Returns:
        pd.DataFrame: [store_id, sku_id, forecast_date, baseline_units, promo_multiplier, holiday_multiplier, predicted_units]
    """
    if not isinstance(horizon_days, int) or horizon_days <= 0 or horizon_days > 365:
        raise ValueError(f"horizon_days must be a positive integer between 1 and 365, got {horizon_days}")

    output_cols = [
        "store_id",
        "sku_id",
        "forecast_date",
        "baseline_units",
        "promo_multiplier",
        "holiday_multiplier",
        "predicted_units",
    ]

    if df.empty:
        return pd.DataFrame(columns=output_cols)

    # Do not mutate input DataFrame
    work_df = df.copy()
    work_df["date"] = pd.to_datetime(work_df["date"])
    work_df["units_sold"] = pd.to_numeric(work_df["units_sold"], errors="coerce").fillna(0.0)

    # Hierarchical cold-start reference averages
    global_avg = float(work_df["units_sold"].mean()) if not work_df["units_sold"].empty else 0.0
    store_avgs = work_df.groupby("store_id")["units_sold"].mean().to_dict()
    sku_avgs = work_df.groupby("sku_id")["units_sold"].mean().to_dict()

    holiday_mult = 1.15 if is_holiday_week else 1.0

    records = []

    for (store_id, sku_id), group in work_df.groupby(["store_id", "sku_id"]):
        group = group.sort_values("date")
        if group.empty:
            continue

        last_date = group["date"].max()
        group_obs_count = len(group)

        # Baseline & Day-of-week seasonality
        if group_obs_count >= 7:
            # Recent 7-day moving average
            recent_7 = group.tail(7)["units_sold"]
            base_demand = float(recent_7.mean()) if len(recent_7) > 0 else 0.0

            series_mean = float(group["units_sold"].mean())
            dow_means = group.groupby(group["date"].dt.dayofweek)["units_sold"].mean()

            dow_factors = {}
            for dow in range(7):
                if series_mean > 0 and dow in dow_means.index:
                    dow_factors[dow] = float(dow_means[dow] / series_mean)
                else:
                    dow_factors[dow] = 1.0
        else:
            # Cold-start hierarchy:
            # 1. Available group mean
            # 2. SKU average
            # 3. Store average
            # 4. Global average
            # 5. 0.0
            if group_obs_count > 0 and not np.isnan(group["units_sold"].mean()):
                base_demand = float(group["units_sold"].mean())
            elif sku_id in sku_avgs and not np.isnan(sku_avgs[sku_id]):
                base_demand = float(sku_avgs[sku_id])
            elif store_id in store_avgs and not np.isnan(store_avgs[store_id]):
                base_demand = float(store_avgs[store_id])
            elif not np.isnan(global_avg):
                base_demand = float(global_avg)
            else:
                base_demand = 0.0

            # Default flat seasonality when history is sparse
            dow_factors = {dow: 1.0 for dow in range(7)}

        # Store-specific promotion multiplier
        promo_mult = 1.0
        if promo_boost and store_id in promo_boost:
            p_val = float(promo_boost[store_id])
            if p_val >= 1.0:
                promo_mult = p_val

        for h in range(1, horizon_days + 1):
            f_date = last_date + pd.Timedelta(days=h)
            dow = f_date.dayofweek
            seasonality = dow_factors.get(dow, 1.0)

            raw_baseline = round(max(0.0, base_demand * seasonality), 2)
            predicted = round(max(0.0, raw_baseline * promo_mult * holiday_mult), 2)

            records.append({
                "store_id": str(store_id),
                "sku_id": str(sku_id),
                "forecast_date": f_date.strftime("%Y-%m-%d"),
                "baseline_units": raw_baseline,
                "promo_multiplier": round(promo_mult, 2),
                "holiday_multiplier": round(holiday_mult, 2),
                "predicted_units": predicted,
            })

    result_df = pd.DataFrame(records, columns=output_cols)
    # Ensure no NaN or infinite values
    result_df["baseline_units"] = result_df["baseline_units"].fillna(0.0).clip(lower=0.0)
    result_df["predicted_units"] = result_df["predicted_units"].fillna(0.0).clip(lower=0.0)

    return result_df


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backend.data_loader import load_demand_data

    print("=" * 70)
    print("DEMAND FORECASTING - BASELINE EXECUTION CHECK")
    print("=" * 70)
    demand_df = load_demand_data()
    print(f"Loaded demand dataset shape: {demand_df.shape}")

    forecast_out = forecast_demand(
        demand_df,
        horizon_days=7,
        promo_boost={"STORE_1": 1.30},
        is_holiday_week=True,
    )
    print("\n--- Forecast Head (First 5 Rows) ---")
    print(forecast_out.head().to_string(index=False))

    print(f"\nTotal Forecast Rows: {len(forecast_out):,}")
    print(f"Unique Stores: {forecast_out['store_id'].nunique()}")
    print(f"Unique SKUs  : {forecast_out['sku_id'].nunique()}")
    print(f"Forecast Horizon Dates: {forecast_out['forecast_date'].nunique()}")

    # Evaluation demonstration
    sample_actual = demand_df.tail(len(forecast_out))["units_sold"].values
    sample_pred = forecast_out["predicted_units"].values
    metrics = calculate_forecast_metrics(sample_actual, sample_pred)
    print(f"\nEvaluation Metrics (MAE, RMSE, WAPE): {metrics}")
    print("=" * 70)
