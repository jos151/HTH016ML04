"""Inventory allocation and optimization using proportional sharing or linear programming."""

import pandas as pd
import numpy as np
import pulp


def allocate_inventory(
    forecast_df: pd.DataFrame,
    total_available_units: float,
) -> pd.DataFrame:
    """Allocates inventory across stores based on forecasted demand and available supply.

    - Sums predicted_units per store across SKUs and dates.
    - If supply >= total demand, allocates exactly what's forecasted.
    - If supply < total demand, allocates proportionally to each store's share of total demand.
    - Computes shortage = max(0, demand - allocated) and excess = max(0, allocated - demand).

    Returns:
        pd.DataFrame: [store_id, forecasted_demand, allocated_units, shortage, excess]
    """
    if forecast_df.empty:
        return pd.DataFrame(
            columns=["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
        )

    # Sum forecasted demand per store across SKUs/days
    summary = (
        forecast_df.groupby("store_id", as_index=False)["predicted_units"]
        .sum()
        .rename(columns={"predicted_units": "forecasted_demand"})
    )

    total_demand = summary["forecasted_demand"].sum()

    if total_demand == 0:
        summary["allocated_units"] = 0.0
    elif total_available_units >= total_demand:
        summary["allocated_units"] = summary["forecasted_demand"]
    else:
        summary["allocated_units"] = (
            summary["forecasted_demand"] / total_demand
        ) * total_available_units

    summary["forecasted_demand"] = summary["forecasted_demand"].round(2)
    summary["allocated_units"] = summary["allocated_units"].round(2)

    summary["shortage"] = (
        (summary["forecasted_demand"] - summary["allocated_units"])
        .clip(lower=0.0)
        .round(2)
    )
    summary["excess"] = (
        (summary["allocated_units"] - summary["forecasted_demand"])
        .clip(lower=0.0)
        .round(2)
    )

    return summary[
        ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
    ]


def allocate_inventory_lp(
    forecast_df: pd.DataFrame,
    total_available_units: float,
    shortage_cost: float = 1.0,
    overstock_cost: float = 0.3,
) -> pd.DataFrame:
    """Allocates inventory across stores using linear programming (PuLP).

    Minimizes total weighted penalty:
        sum_s (shortage_cost * shortage_s + overstock_cost * excess_s)
    Subject to:
        sum_s (allocated_s) <= total_available_units
        allocated_s >= 0
        allocated_s - demand_s = excess_s - shortage_s
        excess_s >= 0, shortage_s >= 0

    Returns:
        pd.DataFrame: [store_id, forecasted_demand, allocated_units, shortage, excess]
    """
    if forecast_df.empty:
        return pd.DataFrame(
            columns=["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
        )

    summary = (
        forecast_df.groupby("store_id", as_index=False)["predicted_units"]
        .sum()
        .rename(columns={"predicted_units": "forecasted_demand"})
    )

    prob = pulp.LpProblem("Inventory_Allocation_LP", pulp.LpMinimize)

    stores = summary["store_id"].tolist()
    demands = dict(zip(summary["store_id"], summary["forecasted_demand"]))

    # Decision variables
    allocated = {s: pulp.LpVariable(f"allocated_{s}", lowBound=0) for s in stores}
    shortage = {s: pulp.LpVariable(f"shortage_{s}", lowBound=0) for s in stores}
    excess = {s: pulp.LpVariable(f"excess_{s}", lowBound=0) for s in stores}

    # Objective function: minimize weighted shortage + overstock cost
    prob += pulp.lpSum(
        [
            shortage_cost * shortage[s] + overstock_cost * excess[s]
            for s in stores
        ]
    )

    # Capacity constraint: total allocation <= available supply
    prob += (
        pulp.lpSum([allocated[s] for s in stores]) <= total_available_units,
        "Total_Supply_Constraint",
    )

    # Inventory balance constraint per store
    for s in stores:
        prob += (
            allocated[s] - demands[s] == excess[s] - shortage[s],
            f"Balance_Constraint_{s}",
        )

    # Solve linear program silently
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    # Extract solution values
    allocated_units = [round(float(pulp.value(allocated[s]) or 0.0), 2) for s in stores]
    shortage_units = [round(float(pulp.value(shortage[s]) or 0.0), 2) for s in stores]
    excess_units = [round(float(pulp.value(excess[s]) or 0.0), 2) for s in stores]

    summary["allocated_units"] = allocated_units
    summary["shortage"] = shortage_units
    summary["excess"] = excess_units
    summary["forecasted_demand"] = summary["forecasted_demand"].round(2)

    return summary[
        ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
    ]


if __name__ == "__main__":
    # Test case: Store A=500, B=400, C=300 demand, total_available_units=1000
    test_df = pd.DataFrame({
        "store_id": ["Store A", "Store B", "Store C"],
        "predicted_units": [500.0, 400.0, 300.0],
    })

    print("=== Proportional Allocation (Supply=1000, Total Demand=1200) ===")
    prop_result = allocate_inventory(test_df, total_available_units=1000)
    print(prop_result.to_string(index=False))

    print("\n=== LP Allocation (PuLP) (shortage_cost=1.0, overstock_cost=0.3) ===")
    lp_result = allocate_inventory_lp(
        test_df,
        total_available_units=1000,
        shortage_cost=1.0,
        overstock_cost=0.3,
    )
    print(lp_result.to_string(index=False))
