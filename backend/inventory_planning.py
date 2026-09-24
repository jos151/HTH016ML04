"""
Inventory planning, safety stock, reorder point recommendations,
fairness indicators, and financial business impact analytics.
"""

import math
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


# Standard normal distribution critical values (Z-scores) for target service levels
SERVICE_LEVEL_Z: Dict[float, float] = {
    0.80: 0.8416,
    0.85: 1.0364,
    0.90: 1.2816,
    0.95: 1.6449,
    0.98: 2.0537,
    0.99: 2.3263,
}


def get_z_score(service_level: float) -> float:
    """Retrieves or approximates standard normal Z-score for a given service level."""
    # Find closest known service level or interpolate safely
    if service_level in SERVICE_LEVEL_Z:
        return SERVICE_LEVEL_Z[service_level]
    # Simple clamped approximation between 0.50 and 0.999
    sl = max(0.50, min(0.999, float(service_level)))
    if sl <= 0.80:
        return 0.8416
    elif sl <= 0.90:
        return 0.8416 + (sl - 0.80) * 4.40
    elif sl <= 0.95:
        return 1.2816 + (sl - 0.90) * 7.26
    elif sl <= 0.98:
        return 1.6449 + (sl - 0.95) * 13.62
    else:
        return 2.0537 + (sl - 0.98) * 27.26


def calculate_safety_stock_and_reorder(
    historical_df: pd.DataFrame,
    current_inventory: Optional[Dict[str, float]] = None,
    lead_time_days: int = 7,
    target_service_level: float = 0.95,
    min_order_qty: int = 10,
    pack_size: int = 5,
) -> pd.DataFrame:
    """Calculates safety stock, reorder points, and replenishment recommendations.

    Formulas:
        lead_time_demand = avg_daily_demand * lead_time_days
        safety_stock = Z * demand_std * sqrt(lead_time_days)
        reorder_point = lead_time_demand + safety_stock
        suggested_order_qty = max(0, reorder_point - current_stock), rounded up to pack_size

    Urgency classification:
        - 'Immediate reorder': current_stock <= safety_stock
        - 'Reorder soon'     : current_stock <= reorder_point
        - 'Monitor'          : reorder_point < current_stock <= 1.5 * reorder_point
        - 'No action'        : current_stock > 1.5 * reorder_point
    """
    if lead_time_days <= 0:
        raise ValueError(f"lead_time_days must be positive, got {lead_time_days}")
    if not (0.50 <= target_service_level < 1.0):
        raise ValueError(f"target_service_level must be between 0.50 and 0.999, got {target_service_level}")

    z = get_z_score(target_service_level)
    sqrt_lt = math.sqrt(lead_time_days)

    records = []
    # Group by SKU across recent history
    grouped = historical_df.groupby("sku_id")

    for sku_id, group in grouped:
        daily_units = group.groupby("date")["units_sold"].sum()
        avg_daily = float(daily_units.mean()) if len(daily_units) > 0 else 0.0
        std_daily = float(daily_units.std(ddof=1)) if len(daily_units) > 1 else (avg_daily * 0.25)
        if math.isnan(std_daily) or std_daily < 0:
            std_daily = avg_daily * 0.25

        ltd = avg_daily * lead_time_days
        ss = z * std_daily * sqrt_lt
        rop = ltd + ss

        curr_stock = 0.0
        if current_inventory and str(sku_id) in current_inventory:
            curr_stock = float(current_inventory[str(sku_id)])
        else:
            # Fallback estimation based on ~10 days demand if not provided
            curr_stock = round(avg_daily * 10.0)

        # Reorder quantity recommendation
        net_shortfall = max(0.0, rop - curr_stock)
        if net_shortfall > 0:
            raw_order = max(float(min_order_qty), net_shortfall)
            # Round up to nearest pack size
            suggested_qty = int(math.ceil(raw_order / max(1, pack_size)) * max(1, pack_size))
        else:
            suggested_qty = 0

        # Days of cover
        days_cover = round(curr_stock / avg_daily, 1) if avg_daily > 0 else 999.0

        # Urgency classification
        if curr_stock <= ss:
            urgency = "Immediate reorder"
            action = f"Stock ({int(curr_stock)}) is below safety stock ({int(round(ss))}). Order {suggested_qty} units immediately."
        elif curr_stock <= rop:
            urgency = "Reorder soon"
            action = f"Stock is below reorder point ({int(round(rop))}). Initiate purchase order for {suggested_qty} units."
        elif curr_stock <= 1.5 * rop:
            urgency = "Monitor"
            action = f"Inventory adequate ({days_cover} days cover). Monitor consumption velocity."
        else:
            urgency = "No action"
            action = f"Stock is healthy ({days_cover} days cover). No replenishment required."

        records.append({
            "sku_id": str(sku_id),
            "avg_daily_demand": round(avg_daily, 2),
            "demand_std_dev": round(std_daily, 2),
            "lead_time_days": int(lead_time_days),
            "lead_time_demand": round(ltd, 1),
            "safety_stock": int(round(ss)),
            "reorder_point": int(round(rop)),
            "current_inventory": int(round(curr_stock)),
            "suggested_order_qty": int(suggested_qty),
            "days_of_cover": days_cover,
            "urgency": urgency,
            "recommended_action": action,
            "service_level_target": float(target_service_level),
            "z_score": round(z, 4),
        })

    out_df = pd.DataFrame(records).sort_values("sku_id").reset_index(drop=True)
    return out_df


def calculate_business_cost_impact(
    total_demand: float,
    total_allocated: float,
    total_shortage: float,
    total_excess: float,
    remaining_inventory: float,
    shortage_cost_per_unit: float = 1.0,
    overstock_cost_per_unit: float = 0.3,
    unit_selling_price: float = 25.0,
    unit_cost: float = 15.0,
) -> Dict[str, Any]:
    """Calculates financial and supply-chain cost impact metrics based on configurable assumptions."""
    shortage_cost = float(total_shortage * shortage_cost_per_unit)
    excess_cost = float(total_excess * overstock_cost_per_unit)
    holding_cost = float(remaining_inventory * overstock_cost_per_unit)
    lost_revenue = float(total_shortage * unit_selling_price)
    fulfilled_revenue = float(total_allocated * unit_selling_price)
    unit_margin = max(0.0, unit_selling_price - unit_cost)
    lost_margin = float(total_shortage * unit_margin)
    total_penalties = float(shortage_cost + excess_cost + holding_cost)

    return {
        "shortage_cost": round(shortage_cost, 2),
        "excess_cost": round(excess_cost, 2),
        "inventory_holding_cost": round(holding_cost, 2),
        "lost_revenue": round(lost_revenue, 2),
        "fulfilled_revenue": round(fulfilled_revenue, 2),
        "unit_margin": round(unit_margin, 2),
        "lost_margin": round(lost_margin, 2),
        "total_penalty_cost": round(total_penalties, 2),
        "assumptions": {
            "shortage_cost_per_unit": shortage_cost_per_unit,
            "overstock_cost_per_unit": overstock_cost_per_unit,
            "unit_selling_price": unit_selling_price,
            "unit_cost": unit_cost,
        },
    }


def calculate_allocation_fairness(
    allocation_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Calculates fulfillment equity and fairness indicators across stores."""
    if allocation_df.empty or "forecasted_demand" not in allocation_df.columns:
        return {
            "min_fulfillment_pct": 0.0,
            "max_fulfillment_pct": 0.0,
            "avg_fulfillment_pct": 0.0,
            "spread_pct": 0.0,
            "fairness_score": 1.0,
            "underserved_stores": [],
            "best_served_stores": [],
        }

    rates = []
    store_map = {}
    for _, row in allocation_df.iterrows():
        store = str(row["store_id"])
        dem = float(row.get("forecasted_demand", 0.0))
        alloc = float(row.get("allocated_units", 0.0))
        rate = (alloc / dem * 100.0) if dem > 0 else 100.0
        rates.append(rate)
        store_map[store] = rate

    min_rate = float(min(rates)) if rates else 0.0
    max_rate = float(max(rates)) if rates else 0.0
    avg_rate = float(np.mean(rates)) if rates else 0.0
    spread = float(max_rate - min_rate)
    std_rate = float(np.std(rates)) if len(rates) > 1 else 0.0

    # Fairness score: 1.0 is perfectly equal service level, scales down with dispersion
    fairness = max(0.0, min(1.0, 1.0 - (std_rate / max(1.0, avg_rate))))

    sorted_stores = sorted(store_map.items(), key=lambda x: x[1])
    underserved = [s for s, r in sorted_stores if r < avg_rate - 5.0]
    best_served = [s for s, r in sorted_stores if r >= avg_rate + 5.0]

    return {
        "min_fulfillment_pct": round(min_rate, 2),
        "max_fulfillment_pct": round(max_rate, 2),
        "avg_fulfillment_pct": round(avg_rate, 2),
        "spread_pct": round(spread, 2),
        "fairness_score": round(fairness, 3),
        "underserved_stores": underserved,
        "best_served_stores": best_served,
        "store_rates": {s: round(r, 1) for s, r in store_map.items()},
    }
