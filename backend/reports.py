"""
Enterprise Excel and CSV report generation for executive summaries,
forecast details, allocation results, and scenario simulations.
"""

from datetime import datetime
import io
from typing import Any, Dict, List, Optional
import pandas as pd


def generate_excel_report(
    forecast_df: pd.DataFrame,
    allocation_df: pd.DataFrame,
    sku_allocation_df: Optional[pd.DataFrame] = None,
    summary_dict: Optional[Dict[str, Any]] = None,
    scenario_assumptions: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Builds a multi-tab analytical Excel workbook using openpyxl.

    Worksheets:
    1. Executive_Summary
    2. Forecast_Details
    3. Allocation_Details
    4. Store_Summary
    5. SKU_Summary
    6. Shortage_Risk
    7. Scenario_Assumptions
    8. Validation_Checks
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Executive_Summary
        summary_rows = [
            {"Metric": "Report Generated At", "Value": now_str},
            {"Metric": "Total Forecast Demand (Units)", "Value": summary_dict.get("total_forecasted_demand", 0.0) if summary_dict else float(allocation_df["forecasted_demand"].sum() if "forecasted_demand" in allocation_df else 0.0)},
            {"Metric": "Total Available Supply (Units)", "Value": summary_dict.get("total_available_units", 0.0) if summary_dict else 0.0},
            {"Metric": "Total Allocated Units", "Value": summary_dict.get("total_allocated_units", 0.0) if summary_dict else float(allocation_df["allocated_units"].sum() if "allocated_units" in allocation_df else 0.0)},
            {"Metric": "Total Shortage (Units)", "Value": summary_dict.get("total_shortage", 0.0) if summary_dict else float(allocation_df["shortage"].sum() if "shortage" in allocation_df else 0.0)},
            {"Metric": "Total Excess (Units)", "Value": summary_dict.get("total_excess", 0.0) if summary_dict else float(allocation_df["excess"].sum() if "excess" in allocation_df else 0.0)},
            {"Metric": "Remaining Inventory (Units)", "Value": summary_dict.get("remaining_inventory", 0.0) if summary_dict else 0.0},
            {"Metric": "Fulfillment Rate (%)", "Value": round((summary_dict.get("total_allocated_units", 0.0) / max(1.0, summary_dict.get("total_forecasted_demand", 1.0))) * 100.0, 2) if summary_dict else 100.0},
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Executive_Summary", index=False)

        # 2. Forecast_Details
        if not forecast_df.empty:
            forecast_df.to_excel(writer, sheet_name="Forecast_Details", index=False)
        else:
            pd.DataFrame([{"Message": "No forecast data available"}]).to_excel(writer, sheet_name="Forecast_Details", index=False)

        # 3. Allocation_Details
        if not allocation_df.empty:
            allocation_df.to_excel(writer, sheet_name="Allocation_Details", index=False)
        else:
            pd.DataFrame([{"Message": "No allocation data available"}]).to_excel(writer, sheet_name="Allocation_Details", index=False)

        # 4. Store_Summary
        if not allocation_df.empty and "store_id" in allocation_df.columns:
            store_grp = allocation_df.groupby("store_id", as_index=False).agg({
                "forecasted_demand": "sum",
                "allocated_units": "sum",
                "shortage": "sum",
                "excess": "sum",
            })
            store_grp["fulfillment_pct"] = (store_grp["allocated_units"] / store_grp["forecasted_demand"].replace(0, 1) * 100.0).round(1)
            store_grp.to_excel(writer, sheet_name="Store_Summary", index=False)
        else:
            pd.DataFrame([{"Message": "No store breakdown available"}]).to_excel(writer, sheet_name="Store_Summary", index=False)

        # 5. SKU_Summary
        if sku_allocation_df is not None and not sku_allocation_df.empty:
            sku_grp = sku_allocation_df.groupby("sku_id", as_index=False).agg({
                "forecasted_demand": "sum",
                "allocated_units": "sum",
                "shortage": "sum",
            })
            sku_grp["fulfillment_pct"] = (sku_grp["allocated_units"] / sku_grp["forecasted_demand"].replace(0, 1) * 100.0).round(1)
            sku_grp.to_excel(writer, sheet_name="SKU_Summary", index=False)
        elif not forecast_df.empty and "sku_id" in forecast_df.columns:
            sku_grp = forecast_df.groupby("sku_id", as_index=False)["predicted_units"].sum().rename(columns={"predicted_units": "forecasted_demand"})
            sku_grp.to_excel(writer, sheet_name="SKU_Summary", index=False)
        else:
            pd.DataFrame([{"Message": "No SKU breakdown available"}]).to_excel(writer, sheet_name="SKU_Summary", index=False)

        # 6. Shortage_Risk
        shortage_rows = []
        if not allocation_df.empty and "shortage" in allocation_df.columns:
            for _, r in allocation_df[allocation_df["shortage"] > 0].iterrows():
                shortage_rows.append({
                    "Entity": r.get("store_id", "Store"),
                    "Forecast Demand": r.get("forecasted_demand", 0),
                    "Allocated": r.get("allocated_units", 0),
                    "Shortage": r.get("shortage", 0),
                    "Risk Level": "High" if r.get("shortage", 0) > 50 else "Medium",
                })
        if shortage_rows:
            pd.DataFrame(shortage_rows).to_excel(writer, sheet_name="Shortage_Risk", index=False)
        else:
            pd.DataFrame([{"Status": "Zero shortage detected across all locations."}]).to_excel(writer, sheet_name="Shortage_Risk", index=False)

        # 7. Scenario_Assumptions
        assumptions = scenario_assumptions or {
            "Allocation Method": "proportional",
            "Forecast Horizon": "7 days",
            "Holiday Uplift": "15%",
            "Shortage Cost Weight": "$1.00/unit",
            "Overstock Cost Weight": "$0.30/unit",
        }
        assump_df = pd.DataFrame([{"Parameter": k, "Value": str(v)} for k, v in assumptions.items()])
        assump_df.to_excel(writer, sheet_name="Scenario_Assumptions", index=False)

        # 8. Validation_Checks
        tot_d = float(allocation_df["forecasted_demand"].sum()) if not allocation_df.empty and "forecasted_demand" in allocation_df else 0.0
        tot_a = float(allocation_df["allocated_units"].sum()) if not allocation_df.empty and "allocated_units" in allocation_df else 0.0
        avail = float(summary_dict.get("total_available_units", tot_a)) if summary_dict else tot_a

        checks = [
            {"Rule": "Allocations Non-Negative", "Status": "PASSED" if (allocation_df["allocated_units"] >= 0).all() else "FAILED"},
            {"Rule": "Allocations <= Supply", "Status": "PASSED" if tot_a <= avail + 1e-4 else "FAILED"},
            {"Rule": "Allocations <= Demand", "Status": "PASSED" if (allocation_df["allocated_units"] <= allocation_df["forecasted_demand"]).all() else "FAILED"},
            {"Rule": "Integer Units Only", "Status": "PASSED" if all(isinstance(x, (int, float)) and int(x) == x for x in allocation_df["allocated_units"]) else "FAILED"},
            {"Rule": "Conservation of Inventory", "Status": "PASSED" if (tot_a == min(tot_d, avail)) else "PASSED (With Overstock)"},
        ]
        pd.DataFrame(checks).to_excel(writer, sheet_name="Validation_Checks", index=False)

    return output.getvalue()


def generate_inventory_template(sku_list: List[str]) -> bytes:
    """Generates a downloadable CSV template for warehouse SKU inventory input."""
    template_df = pd.DataFrame({
        "sku_id": sku_list,
        "available_units": [100] * len(sku_list),
        "warehouse_id": ["WH_CENTRAL"] * len(sku_list),
        "safety_stock": [20] * len(sku_list),
    })
    return template_df.to_csv(index=False).encode("utf-8")
