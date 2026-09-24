"""
Inventory allocation and optimization using proportional sharing with deterministic
largest-remainder integer rounding or linear programming (PuLP).
"""

import math
from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
import pulp


def get_allocation_summary(
    allocated_df: pd.DataFrame,
    total_available_units: float,
) -> Dict[str, float]:
    """Calculates overall summary metrics for an allocation result.

    Returns:
        total_forecasted_demand
        total_available_units
        total_allocated_units
        total_shortage
        total_excess
        remaining_inventory
    """
    if allocated_df.empty:
        return {
            "total_forecasted_demand": 0.0,
            "total_available_units": float(total_available_units),
            "total_allocated_units": 0.0,
            "total_shortage": 0.0,
            "total_excess": 0.0,
            "remaining_inventory": max(0.0, float(total_available_units)),
        }

    tot_demand = float(allocated_df["forecasted_demand"].sum())
    tot_allocated = float(allocated_df["allocated_units"].sum())
    tot_shortage = float(allocated_df["shortage"].sum())
    tot_excess = float(allocated_df["excess"].sum())
    rem_inventory = max(0.0, float(total_available_units) - tot_allocated)

    return {
        "total_forecasted_demand": tot_demand,
        "total_available_units": float(total_available_units),
        "total_allocated_units": tot_allocated,
        "total_shortage": tot_shortage,
        "total_excess": tot_excess,
        "remaining_inventory": rem_inventory,
    }


def allocate_inventory(
    forecast_df: pd.DataFrame,
    total_available_units: float,
) -> pd.DataFrame:
    """Allocates inventory across stores based on forecasted demand and available supply.

    Features:
    1. Rejects negative available inventory with a clear ValueError.
    2. Handles empty forecast DataFrame cleanly.
    3. Aggregates predicted demand by store_id across SKUs and dates.
    4. Rounds allocations to non-negative whole integer units using the
       deterministic largest-remainder method.
    5. If inventory is sufficient (supply >= demand), allocates exact forecasted demand.
    6. If inventory is scarce (supply < demand), allocates proportionally.
    7. No store may receive more than its demand (allocated_units <= forecasted_demand).
    8. Total allocation never exceeds total_available_units.
    9. Under scarcity, uses all available inventory when total demand is positive.
    10. Safe against zero demand without division by zero.
    11. Preserves deterministic ordering by store_id.
    12. Attaches overall summary metrics as DataFrame metadata attribute `.attrs["summary"]`.

    Formula:
        shortage = max(0, forecasted_demand - allocated_units)
        excess = max(0, allocated_units - forecasted_demand)

    Returns:
        pd.DataFrame: [store_id, forecasted_demand, allocated_units, shortage, excess]
    """
    if total_available_units < 0:
        raise ValueError(
            f"total_available_units must be non-negative, got {total_available_units}"
        )

    output_cols = ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]

    if forecast_df.empty:
        empty_res = pd.DataFrame(columns=output_cols)
        empty_res.attrs["summary"] = get_allocation_summary(empty_res, total_available_units)
        return empty_res

    # Validate presence of required columns
    if "store_id" not in forecast_df.columns or "predicted_units" not in forecast_df.columns:
        raise ValueError("forecast_df must contain 'store_id' and 'predicted_units' columns.")

    # 1. Aggregate demand by store
    summary = (
        forecast_df.groupby("store_id", as_index=False)["predicted_units"]
        .sum()
        .rename(columns={"predicted_units": "forecasted_demand"})
    )
    # Ensure deterministic ordering
    summary["store_id"] = summary["store_id"].astype(str)
    summary = summary.sort_values("store_id").reset_index(drop=True)

    summary["forecasted_demand"] = pd.to_numeric(summary["forecasted_demand"], errors="coerce").fillna(0.0)
    summary["forecasted_demand"] = summary["forecasted_demand"].clip(lower=0.0)

    total_demand = summary["forecasted_demand"].sum()
    available_int = int(math.floor(total_available_units))

    # 2. Allocation logic
    if total_demand == 0 or available_int == 0:
        summary["allocated_units"] = 0
    elif total_available_units >= total_demand:
        # Sufficient inventory: allocate exact rounded demand (capped at demand)
        summary["allocated_units"] = summary["forecasted_demand"].apply(lambda d: int(round(d)))
    else:
        # Scarcity: Proportional allocation with Deterministic Largest-Remainder method
        raw_shares = (summary["forecasted_demand"] / total_demand) * available_int
        floored = [int(math.floor(s)) for s in raw_shares]
        rem_units = available_int - sum(floored)

        # Fraction remainders: (remainder, store_id) for deterministic tie-breaking
        ranked_indices = sorted(
            range(len(summary)),
            key=lambda i: (
                raw_shares[i] - floored[i],   # Highest fractional remainder first
                summary.loc[i, "forecasted_demand"],  # Higher demand tie-breaker
                summary.loc[i, "store_id"],   # Alphabetic tie-breaker
            ),
            reverse=True,
        )

        allocated_counts = list(floored)
        for idx in ranked_indices:
            if rem_units <= 0:
                break
            # Ensure allocation does not exceed store demand
            if allocated_counts[idx] < summary.loc[idx, "forecasted_demand"]:
                allocated_counts[idx] += 1
                rem_units -= 1

        summary["allocated_units"] = allocated_counts

    # Format demand and allocations as integer units
    summary["forecasted_demand"] = summary["forecasted_demand"].apply(lambda x: int(round(x)))
    summary["allocated_units"] = summary["allocated_units"].astype(int)

    # 3. Compute shortage and excess
    summary["shortage"] = (
        (summary["forecasted_demand"] - summary["allocated_units"])
        .clip(lower=0)
        .astype(int)
    )
    summary["excess"] = (
        (summary["allocated_units"] - summary["forecasted_demand"])
        .clip(lower=0)
        .astype(int)
    )

    result_df = summary[output_cols]
    result_df.attrs["summary"] = get_allocation_summary(result_df, total_available_units)
    return result_df


def allocate_inventory_lp(
    forecast_df: pd.DataFrame,
    total_available_units: float,
    shortage_cost: float = 1.0,
    overstock_cost: float = 0.3,
    allow_overstock: bool = False,
    fallback_on_solver_error: bool = False,
) -> pd.DataFrame:
    """Allocates inventory across stores using integer linear programming (PuLP).

    Objective:
        Minimize sum_s (shortage_cost * shortage_s + overstock_cost * excess_s)

    Constraints:
        1. Capacity: sum_s (allocated_s) <= total_available_units
        2. Non-negativity: allocated_s >= 0, shortage_s >= 0, excess_s >= 0
        3. Integrality: allocated_s in Integers
        4. Balance: allocated_s - demand_s = excess_s - shortage_s
        5. Overstock policy: allocated_s <= demand_s (unless allow_overstock=True)

    Parameters:
        forecast_df: DataFrame with store_id and predicted_units.
        total_available_units: Total inventory units available in central warehouse.
        shortage_cost: Penalty weight per unit of unfulfilled demand.
        overstock_cost: Penalty weight per unit of inventory allocated beyond demand.
        allow_overstock: Whether stores may receive inventory in excess of forecasted demand.
        fallback_on_solver_error: If True, falls back to proportional allocation with a warning.

    Returns:
        pd.DataFrame: [store_id, forecasted_demand, allocated_units, shortage, excess]
    """
    if total_available_units < 0:
        raise ValueError(
            f"total_available_units must be non-negative, got {total_available_units}"
        )

    output_cols = ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]

    if forecast_df.empty:
        empty_res = pd.DataFrame(columns=output_cols)
        empty_res.attrs["summary"] = get_allocation_summary(empty_res, total_available_units)
        return empty_res

    # Validate presence of required columns
    if "store_id" not in forecast_df.columns or "predicted_units" not in forecast_df.columns:
        raise ValueError("forecast_df must contain 'store_id' and 'predicted_units' columns.")

    summary = (
        forecast_df.groupby("store_id", as_index=False)["predicted_units"]
        .sum()
        .rename(columns={"predicted_units": "forecasted_demand"})
    )
    summary["store_id"] = summary["store_id"].astype(str)
    summary = summary.sort_values("store_id").reset_index(drop=True)

    stores = summary["store_id"].tolist()
    demands = dict(zip(summary["store_id"], summary["forecasted_demand"]))

    prob = pulp.LpProblem("Inventory_Allocation_LP", pulp.LpMinimize)

    # Decision variables (Integer allocation, continuous shortage and excess)
    allocated = {s: pulp.LpVariable(f"allocated_{s}", lowBound=0, cat=pulp.LpInteger) for s in stores}
    shortage = {s: pulp.LpVariable(f"shortage_{s}", lowBound=0, cat=pulp.LpContinuous) for s in stores}
    excess = {s: pulp.LpVariable(f"excess_{s}", lowBound=0, cat=pulp.LpContinuous) for s in stores}

    # Objective function: minimize weighted shortage + overstock cost
    prob += pulp.lpSum(
        [
            shortage_cost * shortage[s] + overstock_cost * excess[s]
            for s in stores
        ]
    )

    # Constraint 1: Supply capacity constraint
    prob += (
        pulp.lpSum([allocated[s] for s in stores]) <= total_available_units,
        "Total_Supply_Constraint",
    )

    # Constraint 2: Balance constraint per store
    for s in stores:
        prob += (
            allocated[s] - demands[s] == excess[s] - shortage[s],
            f"Balance_Constraint_{s}",
        )

    # Constraint 3: Disallow overstock unless explicitly configured
    if not allow_overstock:
        for s in stores:
            prob += (
                allocated[s] <= demands[s],
                f"No_Overstock_{s}",
            )

    # Solve linear program with error checking
    try:
        solver = pulp.PULP_CBC_CMD(msg=False)
        if not solver.available():
            raise RuntimeError("PuLP CBC solver binary is unavailable.")
        status = prob.solve(solver)
        if status != pulp.constants.LpStatusOptimal:
            status_name = pulp.LpStatus.get(status, str(status))
            raise RuntimeError(f"PuLP solver terminated with non-optimal status: '{status_name}'.")
    except Exception as exc:
        if fallback_on_solver_error:
            import warnings
            warnings.warn(f"LP solver error: {exc}. Falling back to proportional allocation.")
            fb = allocate_inventory(forecast_df, total_available_units)
            fb.attrs["solver_fallback"] = True
            return fb
        raise RuntimeError(f"Linear programming allocation failed: {exc}") from exc

    allocated_units = [int(round(float(pulp.value(allocated[s]) or 0.0))) for s in stores]
    shortage_units = [int(round(float(pulp.value(shortage[s]) or 0.0))) for s in stores]
    excess_units = [int(round(float(pulp.value(excess[s]) or 0.0))) for s in stores]

    summary["allocated_units"] = pd.Series(allocated_units, dtype=int)
    summary["shortage"] = pd.Series(shortage_units, dtype=int)
    summary["excess"] = pd.Series(excess_units, dtype=int)
    summary["forecasted_demand"] = summary["forecasted_demand"].apply(lambda d: int(round(d))).astype(int)

    result_df = summary[output_cols]
    result_df.attrs["summary"] = get_allocation_summary(result_df, total_available_units)
    return result_df


if __name__ == "__main__":
    print("=" * 70)
    print("INVENTORY ALLOCATION - MANDATORY WORKED EXAMPLE CHECK")
    print("=" * 70)
    worked_df = pd.DataFrame({
        "store_id": ["Store A", "Store B", "Store C"],
        "predicted_units": [500.0, 400.0, 300.0],
    })

    print("Input: Store A=500, Store B=400, Store C=300 (Total Demand=1200)")
    print("Available Inventory: 1000\n")

    res = allocate_inventory(worked_df, total_available_units=1000)
    print(res.to_string(index=False))

    summary_info = res.attrs.get("summary", {})
    print("\n--- Summary Metrics ---")
    for k, v in summary_info.items():
        print(f"  {k:<26}: {v}")
    print("=" * 70)
