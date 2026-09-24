"""Streamlit dashboard interface for demand forecasting and inventory allocation.

Runs standalone on Streamlit Community Cloud by directly importing and executing
backend business logic (data ingestion, forecasting, and optimization).
"""

from pathlib import Path
import random
import sys
import pandas as pd
import streamlit as st

# Ensure repository root is on sys.path for direct module imports on Streamlit Cloud
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.allocation import allocate_inventory, allocate_inventory_lp
from backend.data_loader import load_demand_data
from backend.forecasting import forecast_demand

st.set_page_config(
    page_title="Demand Forecasting & Inventory Allocation",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Demand Forecasting & Inventory Allocation Dashboard")
st.markdown("Monitor store demand forecasts and optimize inventory distribution across retail locations.")

# Sidebar controls
st.sidebar.header("⚙️ Configuration")

total_available_units = st.sidebar.number_input(
    "Total Available Units",
    min_value=0,
    value=1000,
    step=50,
    help="Total warehouse inventory units available for allocation.",
)

is_holiday_week = st.sidebar.toggle(
    "Holiday Week (+15% Uplift)",
    value=False,
    help="Applies a flat +15% demand uplift across all stores.",
)

promo_stores = st.sidebar.multiselect(
    "Stores to Promo-Boost",
    options=["STORE_1", "STORE_2", "STORE_3", "STORE_4", "STORE_5"],
    default=[],
    help="Select stores participating in promotional demand campaigns (+30% boost).",
)

allocation_method = st.sidebar.selectbox(
    "Allocation Method",
    options=["proportional", "lp"],
    index=0,
    help="Proportional allocation or Linear Programming optimization (PuLP).",
)

col_run, col_sim = st.sidebar.columns(2)
run_button = col_run.button("Run", type="primary", use_container_width=True)
sim_button = col_sim.button("Simulate Promotion", use_container_width=True)


def run_pipeline(units: int, is_holiday: bool, method: str, promo_boost: dict = None):
    """Executes data loading, demand forecasting, and inventory allocation directly."""
    raw_df = load_demand_data()
    forecast_df = forecast_demand(
        df=raw_df,
        horizon_days=7,
        promo_boost=promo_boost,
        is_holiday_week=is_holiday,
    )

    if method == "lp":
        alloc_df = allocate_inventory_lp(
            forecast_df=forecast_df,
            total_available_units=units,
        )
    else:
        alloc_df = allocate_inventory(
            forecast_df=forecast_df,
            total_available_units=units,
        )

    return forecast_df, alloc_df


if run_button:
    try:
        with st.spinner("Calculating demand forecast and optimizing inventory allocation..."):
            base_promo = {s: 1.30 for s in promo_stores} if promo_stores else None
            forecast_df, alloc_df = run_pipeline(
                units=total_available_units,
                is_holiday=is_holiday_week,
                method=allocation_method,
                promo_boost=base_promo,
            )

        # Warning banner if total shortage > 0
        total_shortage = alloc_df["shortage"].sum()
        if total_shortage > 0:
            st.warning(
                f"⚠️ **Inventory Shortage Alert:** Total shortage of **{total_shortage:,.2f} units** "
                f"detected across stores. Supply ({total_available_units:,} units) does not fully meet demand."
            )
        else:
            st.success("✅ **Sufficient Supply:** All store demand has been fully satisfied.")

        # Key Metrics Summary
        col1, col2, col3, col4 = st.columns(4)
        total_demand = alloc_df["forecasted_demand"].sum()
        total_allocated = alloc_df["allocated_units"].sum()
        total_excess = alloc_df["excess"].sum()

        col1.metric("Total Forecasted Demand", f"{total_demand:,.2f}")
        col2.metric("Total Supply Allocated", f"{total_allocated:,.2f}")
        col3.metric("Total Shortage", f"{total_shortage:,.2f}")
        col4.metric("Total Excess", f"{total_excess:,.2f}")

        st.divider()

        # Chart 1: Bar chart of forecasted demand per store
        st.subheader("📊 Forecasted Demand per Store")
        demand_chart_data = alloc_df.set_index("store_id")[["forecasted_demand"]]
        st.bar_chart(demand_chart_data)

        # Results Table
        st.subheader("📋 Store Allocation Results")
        table_cols = ["store_id", "forecasted_demand", "allocated_units", "shortage", "excess"]
        st.dataframe(
            alloc_df[table_cols],
            use_container_width=True,
            hide_index=True,
        )

        # Chart 2: Bar chart of shortage vs excess
        st.subheader("⚖️ Shortage vs. Excess per Store")
        shortage_excess_chart = alloc_df.set_index("store_id")[["shortage", "excess"]]
        st.bar_chart(shortage_excess_chart)

    except FileNotFoundError as fnf_err:
        st.error(f"📁 **Dataset File Error:** {fnf_err}")
    except Exception as exc:
        st.error(f"❌ **An unexpected error occurred:** {exc}")

elif sim_button:
    try:
        with st.spinner("Simulating promotional boost on a random store..."):
            base_promo = {s: 1.30 for s in promo_stores} if promo_stores else {}

            # 1. Baseline allocation (Before)
            _, before_df = run_pipeline(
                units=total_available_units,
                is_holiday=is_holiday_week,
                method=allocation_method,
                promo_boost=base_promo if base_promo else None,
            )

            # 2. Pick a random store to promo-boost by +30% (1.30x)
            store_list = before_df["store_id"].tolist()
            chosen_store = random.choice(store_list)
            boost_factor = 1.30

            # 3. Simulated allocation with promo boost (After)
            sim_promo = dict(base_promo)
            sim_promo[chosen_store] = round(sim_promo.get(chosen_store, 1.0) * boost_factor, 2)

            _, after_df = run_pipeline(
                units=total_available_units,
                is_holiday=is_holiday_week,
                method=allocation_method,
                promo_boost=sim_promo,
            )

        # Simulation Banner
        st.info(
            f"🎯 **Promotion Simulation Triggered:** Applied **+30% promo boost (1.30x)** to **{chosen_store}**."
        )

        # Warning banner if total shortage > 0
        total_shortage_after = after_df["shortage"].sum()
        total_shortage_before = before_df["shortage"].sum()
        shortage_diff = total_shortage_after - total_shortage_before

        if total_shortage_after > 0:
            st.warning(
                f"⚠️ **Inventory Shortage Alert:** Total shortage after promotion is **{total_shortage_after:,.2f} units** "
                f"(increased by **+{shortage_diff:,.2f} units** due to promo surge on {chosen_store})."
            )
        else:
            st.success("✅ **Sufficient Supply:** All demand satisfied even with promotional uplift.")

        # Before / After Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        before_demand = before_df["forecasted_demand"].sum()
        after_demand = after_df["forecasted_demand"].sum()
        chosen_before_demand = before_df.loc[before_df["store_id"] == chosen_store, "forecasted_demand"].values[0]
        chosen_after_demand = after_df.loc[after_df["store_id"] == chosen_store, "forecasted_demand"].values[0]
        chosen_before_alloc = before_df.loc[before_df["store_id"] == chosen_store, "allocated_units"].values[0]
        chosen_after_alloc = after_df.loc[after_df["store_id"] == chosen_store, "allocated_units"].values[0]

        col1.metric("Total Demand", f"{after_demand:,.2f}", delta=f"{after_demand - before_demand:+.2f}")
        col2.metric(f"{chosen_store} Demand", f"{chosen_after_demand:,.2f}", delta=f"{chosen_after_demand - chosen_before_demand:+.2f}")
        col3.metric(f"{chosen_store} Allocated", f"{chosen_after_alloc:,.2f}", delta=f"{chosen_after_alloc - chosen_before_alloc:+.2f}")
        col4.metric("Total Shortage", f"{total_shortage_after:,.2f}", delta=f"{shortage_diff:+.2f}", delta_color="inverse")

        st.divider()

        # Before / After Allocation Comparison Chart
        st.subheader("📊 Allocated Units: Before vs. After Promotion")
        comp_chart_df = pd.DataFrame({
            "Before Promo": before_df.set_index("store_id")["allocated_units"],
            "After Promo": after_df.set_index("store_id")["allocated_units"],
        })
        st.bar_chart(comp_chart_df)

        # Comparison Results Table
        st.subheader("📋 Before / After Comparison Table")
        comp_table = pd.merge(
            before_df[["store_id", "forecasted_demand", "allocated_units", "shortage"]],
            after_df[["store_id", "forecasted_demand", "allocated_units", "shortage"]],
            on="store_id",
            suffixes=(" (Before)", " (After)"),
        )
        st.dataframe(comp_table, use_container_width=True, hide_index=True)

        # Shortage vs Excess Chart
        st.subheader("⚖️ Post-Promotion Shortage vs. Excess per Store")
        shortage_excess_chart = after_df.set_index("store_id")[["shortage", "excess"]]
        st.bar_chart(shortage_excess_chart)

    except FileNotFoundError as fnf_err:
        st.error(f"📁 **Dataset File Error:** {fnf_err}")
    except Exception as exc:
        st.error(f"❌ **An error occurred during simulation:** {exc}")

else:
    st.info("👈 Adjust parameters in the sidebar and click **Run** or **Simulate Promotion** to analyze allocations.")
