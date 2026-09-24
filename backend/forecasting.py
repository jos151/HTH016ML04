"""Demand forecasting models and inference logic."""

from typing import Optional
from pathlib import Path
import sys
import pandas as pd
import numpy as np


def forecast_demand(
    df: pd.DataFrame,
    horizon_days: int = 7,
    promo_boost: Optional[dict] = None,
    is_holiday_week: bool = False,
) -> pd.DataFrame:
    """For each (store_id, sku_id), forecasts the next horizon_days using a 7-day
    moving average adjusted by a day-of-week seasonality factor.

    Applies promo_boost multipliers per store_id if given and a flat +15% uplift
    if is_holiday_week is True.

    Returns:
        pd.DataFrame: [store_id, sku_id, forecast_date, predicted_units]
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0.0)

    records = []

    for (store_id, sku_id), group in df.groupby(["store_id", "sku_id"]):
        group = group.sort_values("date")
        if group.empty:
            continue

        last_date = group["date"].max()

        # 7-day moving average baseline (mean of up to the last 7 observed days)
        recent_7 = group.tail(7)["units_sold"]
        base_ma = recent_7.mean() if len(recent_7) > 0 else 0.0

        # Day-of-week seasonality factor: mean sales on day d / overall mean
        series_mean = group["units_sold"].mean()
        dow_means = group.groupby(group["date"].dt.dayofweek)["units_sold"].mean()

        dow_factors = {}
        for dow in range(7):
            if series_mean > 0 and dow in dow_means.index:
                dow_factors[dow] = dow_means[dow] / series_mean
            else:
                dow_factors[dow] = 1.0

        # Store-specific promo multiplier
        promo_mult = 1.0
        if promo_boost and store_id in promo_boost:
            promo_mult = float(promo_boost[store_id])

        # Flat +15% uplift for holiday week
        holiday_mult = 1.15 if is_holiday_week else 1.0

        for h in range(1, horizon_days + 1):
            f_date = last_date + pd.Timedelta(days=h)
            dow = f_date.dayofweek
            seasonality = dow_factors.get(dow, 1.0)

            predicted = base_ma * seasonality * promo_mult * holiday_mult
            predicted = max(0.0, predicted)

            records.append({
                "store_id": store_id,
                "sku_id": sku_id,
                "forecast_date": f_date.strftime("%Y-%m-%d"),
                "predicted_units": round(predicted, 2),
            })

    return pd.DataFrame(
        records,
        columns=["store_id", "sku_id", "forecast_date", "predicted_units"],
    )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backend.data_loader import load_demand_data

    # Load demand data and test for one store
    demand_df = load_demand_data()
    test_store = "STORE_1"
    store_df = demand_df[demand_df["store_id"] == test_store]

    print("=== Test 1: Without Promo Boost & Without Holiday Week ===")
    baseline_forecast = forecast_demand(
        store_df,
        horizon_days=7,
        promo_boost=None,
        is_holiday_week=False,
    )
    print(baseline_forecast.head(10))

    print("\n=== Test 2: With Promo Boost (1.3x) & With Holiday Week (+15%) ===")
    boosted_forecast = forecast_demand(
        store_df,
        horizon_days=7,
        promo_boost={test_store: 1.3},
        is_holiday_week=True,
    )
    print(boosted_forecast.head(10))
