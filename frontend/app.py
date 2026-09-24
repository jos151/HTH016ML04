"""
Streamlit demonstration interface for demand forecasting and inventory allocation.

Connects to the FastAPI backend service to fetch health status, generate forecasts,
compute constrained inventory allocations, and run scenario simulations without duplicating business logic.
"""

import os
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import requests
import streamlit as st

# Attempt in-process TestClient fallback for resilient execution in sandboxed / non-network environments
try:
    from starlette.testclient import TestClient
    from backend.main import app as fastapi_app
    _inprocess_client: Optional[TestClient] = TestClient(fastapi_app)
except Exception:
    _inprocess_client = None

# Backend service configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Inventory-Constrained Demand Forecasting & Allocation",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def fetch_backend_health() -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Fetches backend health status from GET /health with in-process fallback."""
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=1.5)
        if resp.status_code == 200:
            return True, resp.json(), None
    except Exception:
        pass

    if _inprocess_client is not None:
        try:
            resp = _inprocess_client.get("/health")
            if resp.status_code == 200:
                data = resp.json()
                data["_mode"] = "direct-inprocess"
                return True, data, None
        except Exception as exc:
            return False, None, str(exc)

    return False, None, f"Failed to connect to backend service at {API_BASE_URL}"


def call_allocate_api(
    total_available_units: int,
    horizon_days: int,
    is_holiday_week: bool,
    method: str,
    promo_boost: Optional[Dict[str, float]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Calls POST /allocate on FastAPI backend with in-process fallback."""
    payload = {
        "total_available_units": total_available_units,
        "method": method,
        "horizon_days": horizon_days,
        "is_holiday_week": is_holiday_week,
        "promo_boost": promo_boost,
    }
    try:
        resp = requests.post(f"{API_BASE_URL}/allocate", json=payload, timeout=8.0)
        if resp.status_code == 200:
            return True, resp.json(), None
        elif resp.status_code in (400, 422, 501, 503):
            detail = resp.json().get("detail", resp.text)
            return False, None, f"{detail}"
    except Exception:
        pass

    if _inprocess_client is not None:
        try:
            resp = _inprocess_client.post("/allocate", json=payload)
            if resp.status_code == 200:
                return True, resp.json(), None
            else:
                detail = resp.json().get("detail", resp.text)
                return False, None, f"{detail}"
        except Exception as exc:
            return False, None, f"In-process backend execution failed: {exc}"

    return False, None, f"Could not reach backend service at {API_BASE_URL}."


def call_simulate_api(
    total_available_units: int,
    horizon_days: int,
    is_holiday_week: bool,
    promo_boost: Optional[Dict[str, float]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Calls POST /simulate on FastAPI backend with in-process fallback."""
    payload = {
        "total_available_units": total_available_units,
        "horizon_days": horizon_days,
        "is_holiday_week": is_holiday_week,
        "promo_boost": promo_boost,
    }
    try:
        resp = requests.post(f"{API_BASE_URL}/simulate", json=payload, timeout=8.0)
        if resp.status_code == 200:
            return True, resp.json(), None
        elif resp.status_code in (400, 422, 501, 503):
            detail = resp.json().get("detail", resp.text)
            return False, None, f"{detail}"
    except Exception:
        pass

    if _inprocess_client is not None:
        try:
            resp = _inprocess_client.post("/simulate", json=payload)
            if resp.status_code == 200:
                return True, resp.json(), None
            else:
                detail = resp.json().get("detail", resp.text)
                return False, None, f"{detail}"
        except Exception as exc:
            return False, None, f"In-process backend simulation failed: {exc}"

    return False, None, f"Could not reach backend service at {API_BASE_URL}."


# ==============================================================================
# 1. Header & Overview
# ==============================================================================
st.title("📦 Inventory-Constrained Demand Forecasting & Allocation")
st.markdown(
    "A retail supply-chain decision-support system that models multi-store seasonal demand, "
    "evaluates promotional and holiday uplifts, and allocates scarce inventory using largest-remainder integer math."
)

# Backend Health & Data-Source Status
is_healthy, health_info, health_err = fetch_backend_health()

status_col1, status_col2 = st.columns([1, 3])
with status_col1:
    if is_healthy:
        mode_tag = " (In-Process Direct)" if health_info and health_info.get("_mode") == "direct-inprocess" else ""
        st.success(f"🟢 **Backend Online**{mode_tag}")
    else:
        st.error(f"🔴 **Backend Offline** ({health_err})")

with status_col2:
    if is_healthy and health_info:
        st.caption(
            f"**Data Source:** Real Retail POS Sales Records | **Total Rows:** {health_info.get('row_count', 0):,} | "
            f"**Stores:** {health_info.get('store_count', 0)} | **SKUs:** {health_info.get('sku_count', 0)} | "
            f"**Historical Date Range:** {health_info.get('minimum_date')} to {health_info.get('maximum_date')}"
        )
    else:
        st.caption("⚠️ Ensure FastAPI backend is accessible: `python -m uvicorn backend.main:app --port 8000`")

st.divider()


# ==============================================================================
# 2. Sidebar Controls (Pre-populated Baseline)
# ==============================================================================
st.sidebar.header("⚙️ Supply & Demand Parameters")

# Reset Scenario handling
if "reset_trigger" not in st.session_state:
    st.session_state["reset_trigger"] = 0

def handle_reset():
    st.session_state["avail_inv"] = 1000
    st.session_state["horizon"] = 7
    st.session_state["holiday"] = False
    st.session_state["promo_store"] = "None"
    st.session_state["promo_mult"] = 1.30
    st.session_state["alloc_method"] = "proportional"
    st.session_state["show_simulation"] = False
    st.session_state["reset_trigger"] += 1

if st.sidebar.button("🔄 Reset Scenario", use_container_width=True, on_click=handle_reset):
    st.sidebar.info("Scenario parameters reset to baseline defaults.")

# Pre-populated inputs with session state keys
avail_inv_input = st.sidebar.number_input(
    "Available Inventory Units",
    min_value=0,
    max_value=1_000_000,
    value=st.session_state.get("avail_inv", 1000),
    step=50,
    key="avail_inv",
    help="Total central warehouse supply available for allocation across all stores.",
)

horizon_days_input = st.sidebar.slider(
    "Forecast Horizon (Days)",
    min_value=1,
    max_value=30,
    value=st.session_state.get("horizon", 7),
    key="horizon",
    help="Number of days forward to project demand.",
)

holiday_week_input = st.sidebar.toggle(
    "Holiday Week (+15% Uplift)",
    value=st.session_state.get("holiday", False),
    key="holiday",
    help="Applies a +15% demand uplift factor across stores.",
)

st.sidebar.subheader("🎯 Promotional Boost")
store_options = ["None", "STORE_1", "STORE_2", "STORE_3", "STORE_4", "STORE_5"]
promo_store_default = st.session_state.get("promo_store", "None")
promo_store_index = store_options.index(promo_store_default) if promo_store_default in store_options else 0

promo_store_input = st.sidebar.selectbox(
    "Promotion Store Selector",
    options=store_options,
    index=promo_store_index,
    key="promo_store",
    help="Select store participating in marketing promotion.",
)

promo_mult_input = st.sidebar.slider(
    "Promotion Multiplier",
    min_value=1.00,
    max_value=2.00,
    value=st.session_state.get("promo_mult", 1.30),
    step=0.05,
    key="promo_mult",
    help="Demand multiplier for promoted store (e.g. 1.30 = +30% boost).",
)

st.sidebar.subheader("📐 Allocation Strategy")
method_options = ["proportional", "lp"]
method_default = st.session_state.get("alloc_method", "proportional")
method_index = method_options.index(method_default) if method_default in method_options else 0

method_input = st.sidebar.selectbox(
    "Allocation Method",
    options=method_options,
    index=method_index,
    key="alloc_method",
    help="Proportional largest-remainder integer allocation. (LP disabled in current stage).",
)

col_run, col_sim = st.sidebar.columns(2)
run_button = col_run.button("🚀 Run Forecast & Allocation", type="primary", use_container_width=True)
sim_button = col_sim.button("📊 Simulate Promotion", use_container_width=True)

if sim_button:
    st.session_state["show_simulation"] = True
if run_button:
    st.session_state["show_simulation"] = False


# ==============================================================================
# 3. Main Dashboard Execution & Presentation
# ==============================================================================

if not is_healthy:
    st.error(
        f"⚠️ **Backend Unavailable:** Could not connect to the FastAPI forecasting service ({health_err}). "
        "Please verify that the FastAPI backend is running or dependencies are installed."
    )
else:
    # Build promotional boost configuration
    active_promo = None
    if promo_store_input != "None" and promo_mult_input >= 1.0:
        active_promo = {promo_store_input: float(promo_mult_input)}

    # Call FastAPI Allocation Endpoint
    with st.spinner("Calculating demand forecasts and constrained inventory allocations..."):
        alloc_success, alloc_data, alloc_err = call_allocate_api(
            total_available_units=avail_inv_input,
            horizon_days=horizon_days_input,
            is_holiday_week=holiday_week_input,
            method=method_input,
            promo_boost=active_promo,
        )

    if not alloc_success or not alloc_data:
        st.error(f"❌ **Backend Request Failed:** {alloc_err}")
    else:
        summary = alloc_data["summary"]
        allocations = alloc_data["allocations"]
        df_alloc = pd.DataFrame(allocations)

        tot_demand = summary["total_forecasted_demand"]
        tot_avail = summary["total_available_units"]
        tot_alloc = summary["total_allocated_units"]
        tot_shortage = summary["total_shortage"]
        tot_excess = summary["total_excess"]
        rem_inv = summary["remaining_inventory"]

        # --- User Feedback Banners ---
        if tot_shortage > 0:
            st.warning(
                f"⚠️ **Inventory Shortage Detected:** Total demand ({int(tot_demand):,} units) exceeds available supply "
                f"({int(tot_avail):,} units). Net shortage is **{int(tot_shortage):,} units**. "
                f"Stock has been proportionally allocated using largest-remainder integer distribution."
            )
        else:
            st.success(
                f"✅ **Full Order Fulfillment:** Available inventory ({int(tot_avail):,} units) is sufficient to fulfill "
                f"all forecasted demand ({int(tot_demand):,} units) across all stores with 0 shortage. "
                f"Remaining inventory: {int(rem_inv):,} units."
            )

        # --- KPI Cards (5 required KPIs) ---
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Total Forecast Demand", f"{int(tot_demand):,}")
        kpi2.metric("Inventory Available", f"{int(tot_avail):,}")
        kpi3.metric("Total Allocated Units", f"{int(tot_alloc):,}")
        kpi4.metric(
            "Total Shortage",
            f"{int(tot_shortage):,}",
            delta=f"-{int(tot_shortage):,}" if tot_shortage > 0 else "0",
            delta_color="inverse",
        )
        kpi5.metric("Remaining Inventory", f"{int(rem_inv):,}")

        st.divider()

        # --- Visualizations (Demand, Allocated, Shortage/Excess) ---
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            st.subheader("📊 Forecast Demand by Store")
            chart_demand = df_alloc.set_index("store_id")[["forecasted_demand"]]
            st.bar_chart(chart_demand)

        with vcol2:
            st.subheader("📦 Allocated Quantity by Store")
            chart_alloc = df_alloc.set_index("store_id")[["allocated_units"]]
            st.bar_chart(chart_alloc)

        st.subheader("⚖️ Shortage and Excess by Store")
        chart_shortage = df_alloc.set_index("store_id")[["shortage", "excess"]]
        st.bar_chart(chart_shortage)

        # --- Detailed Allocation Table (Required columns) ---
        st.subheader("📋 Detailed Store Allocation Table")
        display_df = df_alloc.rename(
            columns={
                "store_id": "Store ID",
                "forecasted_demand": "Forecast demand",
                "allocated_units": "Allocated units",
                "shortage": "Shortage",
                "excess": "Excess",
            }
        )[["Store ID", "Forecast demand", "Allocated units", "Shortage", "Excess"]]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()

        # ======================================================================
        # 4. Promotion & Holiday Before-and-After Comparisons
        # ======================================================================
        st.header("🔬 Scenario Before-and-After Impact Analysis")

        # Determine target promotion store for simulation comparison
        sim_promo_store = promo_store_input if promo_store_input != "None" else "STORE_1"
        sim_promo_dict = {sim_promo_store: float(promo_mult_input)}

        with st.spinner("Querying POST /simulate for before-and-after scenarios..."):
            sim_success, sim_data, sim_err = call_simulate_api(
                total_available_units=avail_inv_input,
                horizon_days=horizon_days_input,
                is_holiday_week=holiday_week_input,
                promo_boost=sim_promo_dict,
            )

        if not sim_success or not sim_data:
            st.warning(f"Could not load comparative simulation: {sim_err}")
        else:
            base_s = sim_data["baseline"]
            adj_s = sim_data["adjusted"]
            lift_pct = sim_data["demand_lift_percentage"]
            shortage_change = sim_data["shortage_change"]

            # Tabbed presentation for Promotion and Holiday comparisons
            tab_promo, tab_holiday = st.tabs([
                f"🎯 Promotion Impact ({sim_promo_store} @ {promo_mult_input:.2f}x)",
                "🎉 Holiday Uplift Impact (+15%)",
            ])

            with tab_promo:
                st.subheader(f"Promotion Impact: Baseline vs. {sim_promo_store} (+{int((promo_mult_input-1)*100)}% Boost)")

                p_col1, p_col2, p_col3, p_col4 = st.columns(4)
                p_col1.metric("Baseline Demand", f"{int(base_s['total_demand']):,}")
                p_col2.metric("Promoted Demand", f"{int(adj_s['total_demand']):,}", delta=f"{lift_pct:+.2f}% Lift")
                p_col3.metric("Baseline Shortage", f"{int(base_s['total_shortage']):,}")
                p_col4.metric(
                    "Promoted Shortage",
                    f"{int(adj_s['total_shortage']):,}",
                    delta=f"{shortage_change:+.0f} units",
                    delta_color="inverse",
                )

                df_b = pd.DataFrame(base_s["allocations"]).set_index("store_id")
                df_a = pd.DataFrame(adj_s["allocations"]).set_index("store_id")

                promo_comp_chart = pd.DataFrame({
                    "Baseline Demand": df_b["forecasted_demand"],
                    "Promoted Demand": df_a["forecasted_demand"],
                    "Baseline Allocation": df_b["allocated_units"],
                    "Promoted Allocation": df_a["allocated_units"],
                })
                st.bar_chart(promo_comp_chart)

                promo_comp_table = pd.DataFrame({
                    "Store ID": df_b.index,
                    "Baseline Demand": df_b["forecasted_demand"].values,
                    "Promoted Demand": df_a["forecasted_demand"].values,
                    "Baseline Allocated": df_b["allocated_units"].values,
                    "Promoted Allocated": df_a["allocated_units"].values,
                    "Demand Delta": (df_a["forecasted_demand"] - df_b["forecasted_demand"]).values,
                    "Allocation Delta": (df_a["allocated_units"] - df_b["allocated_units"]).values,
                })
                st.dataframe(promo_comp_table, use_container_width=True, hide_index=True)

            with tab_holiday:
                st.subheader("Holiday Seasonality Impact: Standard Week vs. Holiday Week (+15% Across All Stores)")

                # Fetch clean holiday-only simulation
                with st.spinner("Computing holiday impact comparison..."):
                    h_success, h_data, _ = call_simulate_api(
                        total_available_units=avail_inv_input,
                        horizon_days=horizon_days_input,
                        is_holiday_week=True,
                        promo_boost=None,
                    )

                if h_success and h_data:
                    h_base = h_data["baseline"]
                    h_adj = h_data["adjusted"]
                    h_lift = h_data["demand_lift_percentage"]
                    h_short_diff = h_data["shortage_change"]

                    h_col1, h_col2, h_col3, h_col4 = st.columns(4)
                    h_col1.metric("Standard Demand", f"{int(h_base['total_demand']):,}")
                    h_col2.metric("Holiday Demand", f"{int(h_adj['total_demand']):,}", delta=f"{h_lift:+.2f}% Lift")
                    h_col3.metric("Standard Shortage", f"{int(h_base['total_shortage']):,}")
                    h_col4.metric(
                        "Holiday Shortage",
                        f"{int(h_adj['total_shortage']):,}",
                        delta=f"{h_short_diff:+.0f} units",
                        delta_color="inverse",
                    )

                    df_hb = pd.DataFrame(h_base["allocations"]).set_index("store_id")
                    df_ha = pd.DataFrame(h_adj["allocations"]).set_index("store_id")

                    hol_chart = pd.DataFrame({
                        "Standard Week Allocation": df_hb["allocated_units"],
                        "Holiday Week Allocation": df_ha["allocated_units"],
                    })
                    st.bar_chart(hol_chart)

                    hol_table = pd.DataFrame({
                        "Store ID": df_hb.index,
                        "Standard Demand": df_hb["forecasted_demand"].values,
                        "Holiday Demand": df_ha["forecasted_demand"].values,
                        "Standard Allocated": df_hb["allocated_units"].values,
                        "Holiday Allocated": df_ha["allocated_units"].values,
                        "Demand Uplift": (df_ha["forecasted_demand"] - df_hb["forecasted_demand"]).values,
                    })
                    st.dataframe(hol_table, use_container_width=True, hide_index=True)
                else:
                    st.info("Holiday simulation data available once backend finishes processing.")
