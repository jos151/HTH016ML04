"""Streamlit dashboard interface for demand forecasting and inventory allocation."""

import json
import random
import urllib.request
import urllib.error
import streamlit as st
import pandas as pd

import os

API_BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

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
    help="Select stores participating in promotional demand campaigns.",
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


def fetch_forecast(horizon_days: int = 7, holiday: bool = False):
    url = f"{API_BASE_URL}/forecast?horizon_days={horizon_days}&is_holiday_week={str(holiday).lower()}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_allocation(units: int, method: str = "proportional", promo_boost: dict = None):
    url = f"{API_BASE_URL}/allocate"
    payload = {"total_available_units": int(units), "method": method}
    if promo_boost:
        payload["promo_boost"] = promo_boost
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def compute_allocation(demand_series: pd.Series, available_units: float) -> pd.DataFrame:
    df = demand_series.to_frame(name="forecasted_demand").reset_index()
    total_demand = df["forecasted_demand"].sum()
    if total_demand == 0:
        df["allocated_units"] = 0.0
    elif available_units >= total_demand:
        df["allocated_units"] = df["forecasted_demand"]
    else:
        df["allocated_units"] = ((df["forecasted_demand"] / total_demand) * available_units).round(2)
    df["shortage"] = (df["forecasted_demand"] - df["allocated_units"]).clip(lower=0.0).round(2)
    df["excess"] = (df["allocated_units"] - df["forecasted_demand"]).clip(lower=0.0).round(2)
    return df


if run_button:
    try:
        with st.spinner("Connecting to API and calculating allocations..."):
            forecast_data = fetch_forecast(horizon_days=7, holiday=is_holiday_week)
            allocation_data = fetch_allocation(units=total_available_units, method=allocation_method)

        forecast_df = pd.DataFrame(forecast_data)
        alloc_df = pd.DataFrame(allocation_data)

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

    except urllib.error.URLError as err:
        st.error(
            f"❌ Unable to connect to backend server at `{API_BASE_URL}`. "
            f"Please make sure FastAPI is running (`python -m uvicorn backend.main:app --port 8000`).\n\n"
            f"Error details: {err}"
        )
    except Exception as exc:
        st.error(f"❌ An error occurred: {exc}")

elif sim_button:
    try:
        with st.spinner("Simulating promotional boost on a random store..."):
            # 1. Fetch baseline allocation (before)
            before_data = fetch_allocation(units=total_available_units, method=allocation_method)
            before_df = pd.DataFrame(before_data)

            # 2. Pick a random store to promo-boost by +30% (1.30x)
            store_list = before_df["store_id"].tolist()
            chosen_store = random.choice(store_list)
            boost_factor = 1.30

            # 3. Call endpoint with the promo_boost payload body
            sim_payload = {chosen_store: boost_factor}
            _ = fetch_allocation(
                units=total_available_units,
                method=allocation_method,
                promo_boost=sim_payload,
            )

            # 4. Generate post-promo demand and allocation
            demand_series = before_df.set_index("store_id")["forecasted_demand"].copy()
            demand_series[chosen_store] = round(demand_series[chosen_store] * boost_factor, 2)
            after_df = compute_allocation(demand_series, total_available_units)

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
        chosen_before_alloc = before_df.loc[before_df["store_id"] == chosen_store, "allocated_units"].values[0]
        chosen_after_alloc = after_df.loc[after_df["store_id"] == chosen_store, "allocated_units"].values[0]

        col1.metric("Total Demand", f"{after_demand:,.2f}", delta=f"{after_demand - before_demand:+.2f}")
        col2.metric(f"{chosen_store} Demand", f"{demand_series[chosen_store]:,.2f}", delta=f"+30% promo")
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

    except urllib.error.URLError as err:
        st.error(
            f"❌ Unable to connect to backend server at `{API_BASE_URL}`. "
            f"Please make sure FastAPI is running (`python -m uvicorn backend.main:app --port 8000`).\n\n"
            f"Error details: {err}"
        )
    except Exception as exc:
        st.error(f"❌ An error occurred during simulation: {exc}")

else:
    st.info("👈 Adjust parameters in the sidebar and click **Run** or **Simulate Promotion** to analyze allocations.")
