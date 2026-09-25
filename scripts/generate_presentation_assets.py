"""
Generate high-resolution visual assets and charts for the Hackathon PowerPoint presentation.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = Path("D:/HTH016ML04/reports/presentation_assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Common styling
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.linewidth"] = 1.0


# ------------------------------------------------------------------------------
# Visual 1: Supply Chain Flow (Warehouse -> Stores -> Customers)
# ------------------------------------------------------------------------------
def create_supply_chain_flow():
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.axis("off")

    # Nodes definition: (x, y, width, height, title, subtitle, color, border)
    nodes = [
        (0.08, 0.35, 0.22, 0.35, "Central Warehouse", "Limited Stock (1,000 units)\nSingle Inventory Source", "#1E3A8A", "#0F172A"),
        (0.42, 0.62, 0.22, 0.26, "Store A (High Demand)", "Demand: 500 units\nUrban Flagship", "#0284C7", "#0369A1"),
        (0.42, 0.35, 0.22, 0.26, "Store B (Medium Demand)", "Demand: 400 units\nSuburban Mall", "#0284C7", "#0369A1"),
        (0.42, 0.08, 0.22, 0.26, "Store C (Standard Demand)", "Demand: 300 units\nLocal Outlet", "#0284C7", "#0369A1"),
        (0.76, 0.35, 0.18, 0.35, "End Customers", "Retail Shoppers\nTarget Fill Rate", "#059669", "#047857"),
    ]

    for x, y, w, h, title, sub, bg, border in nodes:
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.04",
            facecolor=bg, edgecolor=border, linewidth=2.0
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.65, title, color="white", fontsize=11, fontweight="bold", ha="center", va="center")
        ax.text(x + w/2, y + h*0.32, sub, color="#E2E8F0", fontsize=8.5, ha="center", va="center")

    # Connectors Warehouse -> Stores
    arrow_props = dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#F97316", lw=2.5)
    ax.annotate("", xy=(0.42, 0.75), xytext=(0.30, 0.58), arrowprops=arrow_props)
    ax.annotate("", xy=(0.42, 0.48), xytext=(0.30, 0.52), arrowprops=arrow_props)
    ax.annotate("", xy=(0.42, 0.21), xytext=(0.30, 0.46), arrowprops=arrow_props)

    # Connectors Stores -> Customers
    arrow_cust = dict(arrowstyle="->,head_width=0.35,head_length=0.5", color="#10B981", lw=2.0)
    ax.annotate("", xy=(0.76, 0.55), xytext=(0.64, 0.75), arrowprops=arrow_cust)
    ax.annotate("", xy=(0.76, 0.52), xytext=(0.64, 0.48), arrowprops=arrow_cust)
    ax.annotate("", xy=(0.76, 0.48), xytext=(0.64, 0.21), arrowprops=arrow_cust)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "slide1_supply_chain_flow.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Saved slide1_supply_chain_flow.png")


# ------------------------------------------------------------------------------
# Visual 2: Problem Demand Gap (1,200 Demand vs 1,000 Available -> 200 Gap)
# ------------------------------------------------------------------------------
def create_problem_gap_chart():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    categories = ["Total Demand\n(Stores A, B, C)", "Available Stock\n(Warehouse Cap)"]
    values = [1200, 1000]
    colors = ["#1E3A8A", "#0284C7"]

    bars = ax.bar(categories, values, color=colors, width=0.45, edgecolor="#0F172A", linewidth=1.5, zorder=3)

    # Values on top of bars
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 25, f"{int(h):,} units", ha="center", va="bottom", fontsize=12, fontweight="bold", color="#0F172A")

    # Shortage gap annotation
    ax.annotate(
        "", xy=(0.25, 1200), xytext=(0.25, 1000),
        arrowprops=dict(arrowstyle="<->,head_width=0.4,head_length=0.6", color="#EA580C", lw=3.0)
    )
    ax.text(0.38, 1100, "Supply Gap: -200 units\n(Unavoidable Shortage)", color="#EA580C", fontsize=11, fontweight="bold", va="center")

    ax.set_ylim(0, 1400)
    ax.set_ylabel("Quantity (Units)", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_title("The Inventory Scarcity Dilemma", fontsize=14, fontweight="bold", color="#0F172A", pad=15)
    ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)

    # Sub-breakdown callout box
    callout_text = "Store A: 500 units (41.7%)\nStore B: 400 units (33.3%)\nStore C: 300 units (25.0%)"
    ax.text(0.95, 0.25, callout_text, transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#EFF6FF", edgecolor="#3B82F6", linewidth=1.5),
            ha="right", va="center", color="#1E3A8A", fontweight="bold")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "slide2_demand_gap_chart.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Saved slide2_demand_gap_chart.png")


# ------------------------------------------------------------------------------
# Visual 3: Solution Workflow Diagram
# ------------------------------------------------------------------------------
def create_solution_workflow():
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.axis("off")

    steps = [
        ("1. Historical Sales", "POS transactions\nCartesian clean grid", "#1E3A8A"),
        ("2. Demand Forecast", "7-day rolling baseline\nDay-of-week seasonality", "#1D4ED8"),
        ("3. Lifts & Scenarios", "Promo (+30%)\nHoliday week (+15%)", "#0284C7"),
        ("4. Inventory Input", "Warehouse stock cap\nUser available units", "#D97706"),
        ("5. Rationing Engine", "Largest-Remainder Quota\nOptional PuLP MILP", "#059669"),
        ("6. Decision Output", "Store allocations\nShortage & reports", "#047857"),
    ]

    n = len(steps)
    box_w = 0.13
    box_h = 0.55
    spacing = (1.0 - 0.05 * 2 - n * box_w) / (n - 1)

    for i, (title, sub, col) in enumerate(steps):
        x = 0.05 + i * (box_w + spacing)
        y = 0.22
        rect = patches.FancyBboxPatch(
            (x, y), box_w, box_h,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            facecolor=col, edgecolor="#0F172A", linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + box_w/2, y + box_h * 0.72, title, color="white", fontsize=9.5, fontweight="bold", ha="center", va="center")
        ax.text(x + box_w/2, y + box_h * 0.35, sub, color="#E2E8F0", fontsize=7.5, ha="center", va="center")

        if i < n - 1:
            arr_x = x + box_w + 0.005
            arr_w = spacing - 0.01
            ax.annotate("", xy=(arr_x + arr_w, y + box_h/2), xytext=(arr_x, y + box_h/2),
                        arrowprops=dict(arrowstyle="->,head_width=0.3,head_length=0.4", color="#F97316", lw=2.0))

    # Core allocation principle box at bottom
    ax.text(0.5, 0.08, "Core Principle: Each store receives whole units strictly proportional to its forecast demand share.",
            fontsize=10.5, fontweight="bold", ha="center", va="center", color="#0F172A",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=1.2))

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "slide3_solution_workflow.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Saved slide3_solution_workflow.png")


# ------------------------------------------------------------------------------
# Visual 4: High-Fidelity Web Application UI Representation
# ------------------------------------------------------------------------------
def create_dashboard_mockup():
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#0F172A")
    ax.axis("off")

    # Header bar
    header = patches.Rectangle((0.02, 0.90), 0.96, 0.08, facecolor="#1E293B", edgecolor="#334155", linewidth=1.5)
    ax.add_patch(header)
    ax.text(0.04, 0.94, "Inventory-Constrained Demand Forecasting & Allocation Platform", color="white", fontsize=11, fontweight="bold", va="center")
    ax.text(0.96, 0.94, "[ONLINE] Backend Active | 5 Stores | 10 SKUs", color="#34D399", fontsize=9, fontweight="bold", ha="right", va="center")

    # Left sidebar
    sidebar = patches.Rectangle((0.02, 0.04), 0.22, 0.84, facecolor="#1E293B", edgecolor="#334155", linewidth=1.5)
    ax.add_patch(sidebar)
    ax.text(0.04, 0.84, "PARAMETERS", color="#94A3B8", fontsize=9, fontweight="bold")
    ax.text(0.04, 0.77, "Available Inventory:\n[ 1,000 units ]", color="white", fontsize=8.5)
    ax.text(0.04, 0.67, "Forecast Horizon:\n[ 7 Days ]", color="white", fontsize=8.5)
    ax.text(0.04, 0.57, "Allocation Method:\n[ Proportional (LP) ]", color="white", fontsize=8.5)
    ax.text(0.04, 0.47, "Promotion Store:\n[ STORE_1 (+30%) ]", color="white", fontsize=8.5)
    ax.text(0.04, 0.37, "Holiday Week:\n[ Enabled (+15%) ]", color="white", fontsize=8.5)
    ax.text(0.04, 0.25, "NAVIGATION", color="#94A3B8", fontsize=9, fontweight="bold")
    ax.text(0.04, 0.18, "- Executive Dashboard\n- Demand Forecasting\n- Inventory Allocation\n- Scenario Simulator\n- Reports & Exports", color="#38BDF8", fontsize=7.5)

    # Main area - KPI cards
    kpi_defs = [
        (0.26, "Total Demand", "1,200", "#38BDF8"),
        (0.44, "Total Allocated", "1,000", "#34D399"),
        (0.62, "System Shortage", "200", "#F97316"),
        (0.80, "Fill Rate", "83.3%", "#A78BFA"),
    ]
    for x, title, val, col in kpi_defs:
        card = patches.FancyBboxPatch((x, 0.74), 0.16, 0.14, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor="#1E293B", edgecolor="#334155", linewidth=1.2)
        ax.add_patch(card)
        ax.text(x + 0.08, 0.83, title, color="#94A3B8", fontsize=8, ha="center", va="center")
        ax.text(x + 0.08, 0.78, val, color=col, fontsize=14, fontweight="bold", ha="center", va="center")

    # Main area - Chart 1: Store Allocation Breakdown
    chart1 = patches.FancyBboxPatch((0.26, 0.28), 0.42, 0.43, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor="#1E293B", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(chart1)
    ax.text(0.28, 0.67, "Store-Level Allocation vs Demand", color="white", fontsize=9.5, fontweight="bold")

    # Mini bars inside chart 1
    stores = ["Store A", "Store B", "Store C"]
    demands = [500, 400, 300]
    allocs = [417, 333, 250]
    for idx, (s, d, a) in enumerate(zip(stores, demands, allocs)):
        bx = 0.29 + idx * 0.12
        # Demand bar (grey)
        ax.add_patch(patches.Rectangle((bx, 0.32), 0.04, (d/500)*0.28, facecolor="#475569"))
        # Alloc bar (green)
        ax.add_patch(patches.Rectangle((bx + 0.045, 0.32), 0.04, (a/500)*0.28, facecolor="#10B981"))
        ax.text(bx + 0.04, 0.30, s, color="#94A3B8", fontsize=7.5, ha="center")

    ax.text(0.58, 0.67, "[Demand]  [Allocated]", color="#94A3B8", fontsize=7.5, ha="right")

    # Main area - Chart 2: Scenario Comparison / Decision Log
    chart2 = patches.FancyBboxPatch((0.70, 0.28), 0.28, 0.43, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor="#1E293B", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(chart2)
    ax.text(0.72, 0.67, "Decision Support & Alerts", color="white", fontsize=9.5, fontweight="bold")
    ax.text(0.72, 0.58, "[!] High Stockout Risk at Store A\n   Shortage: 83 units (Fill: 83.4%)", color="#FDBA74", fontsize=7.5)
    ax.text(0.72, 0.46, "[+] Scenario Uplift Analysis:\n   Promo Boost adds +5.3% Demand", color="#93C5FD", fontsize=7.5)
    ax.text(0.72, 0.35, "[OK] Conservation Enforced:\n   100% of 1,000 units rationed", color="#86EFAC", fontsize=7.5)

    # Bottom table bar
    tbl = patches.FancyBboxPatch((0.26, 0.04), 0.72, 0.21, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor="#1E293B", edgecolor="#334155", linewidth=1.2)
    ax.add_patch(tbl)
    ax.text(0.28, 0.21, "Recommended Store Rationing Schedule (Hare-Niemeyer Integer Math)", color="white", fontsize=9, fontweight="bold")
    ax.text(0.28, 0.14, "STORE_A: Demand = 500  |  Allocated = 417 units  |  Shortage = 83  |  Fill = 83.4%", color="#E2E8F0", fontsize=8)
    ax.text(0.28, 0.09, "STORE_B: Demand = 400  |  Allocated = 333 units  |  Shortage = 67  |  Fill = 83.3%", color="#E2E8F0", fontsize=8)
    ax.text(0.28, 0.05, "STORE_C: Demand = 300  |  Allocated = 250 units  |  Shortage = 50  |  Fill = 83.3%", color="#E2E8F0", fontsize=8)

    # Mockup badge
    ax.text(0.98, 0.02, "Design Representation: Streamlit Web Dashboard", color="#64748B", fontsize=7.5, ha="right", style="italic")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "slide4_dashboard_mockup.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Saved slide4_dashboard_mockup.png")


# ------------------------------------------------------------------------------
# Visual 5: Allocation Results Grouped Bar Chart
# ------------------------------------------------------------------------------
def create_allocation_results_chart():
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    stores = ["Store A", "Store B", "Store C", "Total System"]
    demands = [500, 400, 300, 1200]
    allocated = [417, 333, 250, 1000]
    shortage = [83, 67, 50, 200]

    x = np.arange(len(stores))
    width = 0.26

    rects1 = ax.bar(x - width, demands, width, label="Forecast Demand", color="#1E3A8A", edgecolor="#0F172A", zorder=3)
    rects2 = ax.bar(x, allocated, width, label="Allocated Stock", color="#059669", edgecolor="#064E3B", zorder=3)
    rects3 = ax.bar(x + width, shortage, width, label="Shortage", color="#EA580C", edgecolor="#9A3412", zorder=3)

    # Value labels on bars
    for rects, col in [(rects1, "#0F172A"), (rects2, "#064E3B"), (rects3, "#9A3412")]:
        for r in rects:
            h = r.get_height()
            ax.text(r.get_x() + r.get_width()/2, h + 15, str(int(h)), ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=col)

    ax.set_ylabel("Units", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_title("Controlled Demonstration: Proportional Inventory Allocation", fontsize=13, fontweight="bold", color="#0F172A", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(stores, fontsize=10, fontweight="bold", color="#1E293B")
    ax.legend(frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=9.5)
    ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
    ax.set_ylim(0, 1400)

    # Note at bottom
    ax.text(0.5, -0.15, "Controlled demonstration of proportional allocation (Total Supply: 1,000 | Deterministic Integer Units)",
            transform=ax.transAxes, ha="center", fontsize=8.5, style="italic", color="#475569")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "slide5_allocation_barchart.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Saved slide5_allocation_barchart.png")


# ------------------------------------------------------------------------------
# Visual 6: Impact & Future Scope Framework
# ------------------------------------------------------------------------------
def create_impact_scope_visual():
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.axis("off")

    cards = [
        (0.04, "Business Impact", [
            "- Better use of limited inventory",
            "- Reduced stockout risk at key stores",
            "- Fair, demand-aligned distribution",
            "- Fast scenario-based decisions",
        ], "#0284C7", "#E0F2FE"),
        (0.37, "Current Limitations", [
            "- Historical data quality dependent",
            "- Single-warehouse tier modeled",
            "- Current stock user-provided",
            "- 5 stores & 10 SKUs scope",
        ], "#EA580C", "#FFEDD5"),
        (0.70, "Future Scope", [
            "- Multi-warehouse network optimization",
            "- Advanced ML forecasting (DeepAR)",
            "- Automated supplier lead-time ROP",
            "- Android mobile app deployment",
        ], "#059669", "#D1FAE5"),
    ]

    for x, title, bullets, border_col, bg_col in cards:
        rect = patches.FancyBboxPatch(
            (x, 0.12), 0.26, 0.78,
            boxstyle="round,pad=0.03,rounding_size=0.04",
            facecolor=bg_col, edgecolor=border_col, linewidth=2.0
        )
        ax.add_patch(rect)
        ax.text(x + 0.13, 0.82, title, color=border_col, fontsize=11, fontweight="bold", ha="center", va="center")
        bullet_text = "\n\n".join(bullets)
        ax.text(x + 0.02, 0.48, bullet_text, color="#1E293B", fontsize=8.5, va="center")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "slide6_impact_summary.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Saved slide6_impact_summary.png")


if __name__ == "__main__":
    create_supply_chain_flow()
    create_problem_gap_chart()
    create_solution_workflow()
    create_dashboard_mockup()
    create_allocation_results_chart()
    create_impact_scope_visual()
    print("All 6 presentation visual assets generated successfully.")
