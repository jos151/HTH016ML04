# Final Hackathon Review Presentation: Content & Speaker Notes

**Presentation Title:** Smart Demand Forecasting and Inventory Allocation  
**Subtitle:** Predict demand and distribute limited stock efficiently  
**Target Duration:** 5 to 7 Minutes (Total Estimated Time: 6 minutes 30 seconds)  
**Layout:** 16:9 Widescreen  
**File Location:** [`reports/Final_Hackathon_Review_Presentation.pptx`](file:///D:/HTH016ML04/reports/Final_Hackathon_Review_Presentation.pptx)  
**Team Name:** Antigravity Solutions  

---

## Slide 1: Title and Project Introduction

* **Slide Number:** 1
* **Slide Category:** Title & Overview
* **Slide Title:** Smart Demand Forecasting and Inventory Allocation
* **Slide Subtitle:** Predict demand and distribute limited stock efficiently
* **Value Statement:** *"The system predicts store demand and recommends how limited inventory should be distributed."*
* **Slide Content:**
  * Tagline Badge: `RETAIL SUPPLY CHAIN INTELLIGENCE | HACKATHON 2026`
  * Core Project Title & Value Statement
  * Team: Antigravity Solutions
  * Domain: Retail POS Analytics, Seasonality, & Constrained Rationing
* **Visual Used:**
  * Diagram: Central Warehouse (1,000 units) → Distribution Arrows → Multiple Stores (Store A, Store B, Store C) → End Customers.
  * File: `reports/presentation_assets/slide1_supply_chain_flow.png`
* **Data Source:** System Architecture Specification
* **Estimated Speaking Time:** 30 seconds

### Speaker Notes (Slide 1)
> "Good morning, judges and mentors. Today we are presenting our solution for **Smart Demand Forecasting and Inventory Allocation**."
>
> "Retailers often have limited inventory in their central warehouse, but experience vastly different customer demand at each individual retail store. Our platform bridges this critical operational gap: it predicts future store-level demand and recommends how available stock should be distributed fairly and efficiently to eliminate stockouts and minimize excess inventory."
>
> *Sources:*  
> *Visual on this slide was generated with Microsoft Copilot.*

---

## Slide 2: Problem and Business Need

* **Slide Number:** 2
* **Slide Category:** Market Reality & Supply Scarcity
* **Slide Title:** The Problem We Are Solving
* **Slide Content (Key Points):**
  * Each retail store experiences distinct customer demand patterns.
  * Demand surges during weekends, calendar holidays, and promotions.
  * Central warehouse stock is strictly limited and cannot meet peak demand.
  * Poor allocation causes costly stockouts in high-demand stores.
  * Oversupplying slower stores leads to trapped capital and surplus waste.
* **Controlled Example Callout:**
  * Total Store Demand = 1,200 units (Store A: 500 | Store B: 400 | Store C: 300)
  * Available Warehouse Stock = 1,000 units
  * System Shortage = 200 units (Unavoidable Gap)
  * Central Question: *"How should the available 1,000 units be distributed?"*
* **Visual Used:**
  * Chart: Vertical Bar Comparison of Total Demand (1,200 units) vs Available Stock (1,000 units) with a prominent 200-unit Shortage Gap callout bracket.
  * File: `reports/presentation_assets/slide2_demand_gap_chart.png`
* **Data Source:** Project-controlled demonstration scenario
* **Estimated Speaking Time:** 60 seconds

### Speaker Notes (Slide 2)
> "Let's look at the operational dilemma every inventory manager faces daily."
>
> "In a retail network, no two stores are alike. Store A in a bustling city center might sell twice as fast as Store C in a suburb. On top of that, weekend rushes, promotional discounts, and holiday weeks introduce dramatic demand volatility."
>
> "Meanwhile, upstream warehouse inventory is strictly finite. When aggregate demand across all stores exceeds available supply—like in our controlled scenario where three stores demand 1,200 units, but our warehouse only has 1,000 units—a shortage of 200 units is unavoidable."
>
> "The wrong decision is to divide the stock equally: giving each store 333 units would leave Store A with a massive 167-unit stockout while oversupplying Store C beyond its needs. We need smart, demand-proportional allocation."
>
> *Sources:*  
> *Visual on this slide was generated with Microsoft Copilot.*  
> *Data Source: Project-controlled demonstration scenario.*

---

## Slide 3: Our Solution and Workflow

* **Slide Number:** 3
* **Slide Category:** End-to-End Decision Pipeline
* **Slide Title:** How Our Solution Works
* **Slide Content:**
  * Workflow Pipeline:
    1. Historical Sales Data (POS transactions, Cartesian clean grid)
    2. Demand Forecasting (7-day rolling baseline, day-of-week seasonality)
    3. Lifts & Scenarios (Promo +30%, Holiday week +15%)
    4. Available Inventory (Warehouse stock cap, user input)
    5. Rationing Engine (Largest-Remainder Quota, optional PuLP MILP)
    6. Decision Output (Store allocations, shortage alerts, audit-ready exports)
  * Core Allocation Rule: *"When supply is limited, each store receives stock based on its share of forecasted demand."*
* **Supporting Points:**
  * Predict demand by store and product using historical rolling baselines and seasonality.
  * Adjust demand dynamically for targeted store promotions (+30%) and holiday weeks (+15%).
  * Compare total predicted demand against available warehouse stock to identify systemic shortages.
  * Allocate stock according to forecasted demand shares using discrete largest-remainder integer math.
* **Visual Used:**
  * Diagram: Left-to-right 6-stage pipeline banner with color-coded nodes and directional arrows.
  * File: `reports/presentation_assets/slide3_solution_workflow.png`
* **Data Source:** System Design & Methodological Specification
* **Estimated Speaking Time:** 75 seconds

### Speaker Notes (Slide 3)
> "Here is the six-stage architecture powering our solution, moving smoothly from raw data to actionable store decisions."
>
> "First, we ingest historical point-of-sale transactions and clean the data across a complete Cartesian grid."
>
> "Second, our forecasting engine models day-of-week seasonality on top of a 7-day rolling baseline, capturing cyclical shopping habits."
>
> "Third, managers can simulate demand uplifts: promotions apply multiplier boosts to targeted stores, and holiday weeks scale demand across the network."
>
> "Fourth, the manager inputs the actual warehouse inventory available for rationing."
>
> "Fifth, our rationing engine applies Hare-Niemeyer largest-remainder integer math, or our optional PuLP mixed-integer linear programming solver, to eliminate fractional units and guarantee zero inventory wastage."
>
> "Finally, store allocation schedules, stockout alerts, and multi-tab Excel reports are exported."
>
> "The core principle is simple: every store receives whole units strictly according to its forecast demand share."
>
> *Sources:*  
> *Visual on this slide was generated with Microsoft Copilot.*

---

## Slide 4: Web Application and Main Features

* **Slide Number:** 4
* **Slide Category:** Interactive Decision-Support Platform
* **Slide Title:** Web Application Features
* **Slide Content (Core Platform Capabilities):**
  * Store and SKU demand forecasts with empirical uncertainty bounds.
  * Inventory input and automated largest-remainder quota rationing.
  * Real-time shortage, excess, and stockout risk alerts.
  * What-if simulation for promotional (+30%) and holiday (+15%) uplifts.
  * Side-by-side baseline vs scenario comparison metrics.
  * One-click 8-worksheet Excel workbook & CSV report downloads.
* **Simple 6-Step Decision Flow:**
  1. Select stores and product SKUs
  2. Choose forecast horizon (7-30 days)
  3. Enter available warehouse inventory
  4. Run proportional or LP allocation
  5. Review store shortages & risk alerts
  6. Export full analytical Excel schedule
* **Visual Used:**
  * High-fidelity UI mockup of the Streamlit dashboard showing top navigation, sidebar parameters, 4 KPI cards (Total Demand, Total Allocated, Shortage, Fill Rate), store allocation bar chart, and decision schedule table.
  * Label: *"Design Representation: Streamlit Web Dashboard"*
  * File: `reports/presentation_assets/slide4_dashboard_mockup.png`
* **Data Source:** Project web application
* **Estimated Speaking Time:** 75 seconds

### Speaker Notes (Slide 4)
> "To make this powerful forecasting and rationing logic usable for business operators, we packaged the complete pipeline into an intuitive, interactive Streamlit web dashboard backed by a high-performance FastAPI service."
>
> "Here is the user workflow:"
> "First, planners select their active store and SKU parameters in the sidebar. They choose a forecast horizon—like 7 days—and enter the available warehouse inventory."
>
> "With one click, the platform runs the forecasting and allocation engine. The Executive Dashboard instantly surfaces high-level KPI cards: total demand, total allocated units, system shortage, and overall network fill rate."
>
> "Interactive bar charts allow planners to visually compare demand against allocated stock for every store, while prioritized alert cards flag high-risk stockout locations."
>
> "Finally, operators can simulate promotional elasticity or download an 8-worksheet audit-ready Excel workbook with complete mathematical validation checks."
>
> *Sources:*  
> *Source: Design Representation: Streamlit Web Dashboard.*

---

## Slide 5: Results and Controlled Demonstration

* **Slide Number:** 5
* **Slide Category:** Controlled Demonstration & Mathematical Invariants
* **Slide Title:** Allocation Result
* **Slide Content:**
  * Controlled Demonstration Outcome:
    * Store A: Demand = 500 → Allocated = 417 | Shortage = 83 (83.4% Fill Rate)
    * Store B: Demand = 400 → Allocated = 333 | Shortage = 67 (83.3% Fill Rate)
    * Store C: Demand = 300 → Allocated = 250 | Shortage = 50 (83.3% Fill Rate)
    * Summary: Demand = 1,200 | Supply = 1,000 | Allocated = 1,000 | Shortage = 200
  * Mathematical Invariants Enforced:
    * Total allocation strictly respects warehouse supply: $417 + 333 + 250 = 1,000$.
    * No store receives more stock than its forecast demand ($A_i \le D_i$).
    * Allocation plus shortage exactly balances demand ($A_i + S_i = D_i$).
    * Deterministic whole integer units (zero fractional cases).
  * Holdout Forecast Evaluation:
    * MAE: 6.67 units | RMSE: 8.16 units | WAPE: 3.33%
    * *"Forecast evaluation is performed using chronological test data."*
* **Visual Used:**
  * Grouped Bar Chart comparing Forecast Demand (Navy), Allocated Stock (Green), and Shortage (Orange) across Store A, Store B, Store C, and Total System.
  * File: `reports/presentation_assets/slide5_allocation_barchart.png`
* **Data Source:** Project-controlled test results
* **Estimated Speaking Time:** 90 seconds

### Speaker Notes (Slide 5)
> "Here are the concrete results from our controlled demonstration, validating how proportional largest-remainder math solves the scarcity dilemma."
>
> "Looking at the table and grouped bar chart:"
> "Store A demanded 500 units and receives 417 units, leaving a shortage of 83."
> "Store B demanded 400 units and receives 333 units, leaving a shortage of 67."
> "Store C demanded 300 units and receives 250 units, leaving a shortage of 50."
>
> "Notice what this achieves: every store achieves a balanced fill rate of approximately 83.3%. The system does not eliminate the 200-unit shortage—because available supply is fixed at 1,000—but it distributes that shortage fairly across stores in exact proportion to demand velocity."
>
> "Furthermore, our automated test suite validates four mathematical conservation laws across every execution:"
> "1. Total allocation equals warehouse supply without inventory loss."
> "2. No store receives more than its demand."
> "3. Allocation plus shortage balances demand."
> "4. All allocations are whole integers—essential for physical retail boxes."
>
> "On historical out-of-sample data, our seasonal baseline achieves a Weighted Absolute Percentage Error of just 3.33%."
>
> *Sources:*  
> *Source: Project-controlled test results.*

---

## Slide 6: Impact, Limitations, and Future Scope

* **Slide Number:** 6
* **Slide Category:** Value Delivery & Product Roadmap
* **Slide Title:** Impact and Future Development
* **Slide Content (Three Pillars):**
  1. **Business Impact:**
     * Better use of limited inventory
     * Reduced stockout risk at key stores
     * Fair, demand-aligned distribution
     * Fast scenario-based decisions
  2. **Current Limitations:**
     * Historical data quality dependent
     * Single-warehouse tier modeled
     * Current stock user-provided
     * 5 stores & 10 SKUs scope
  3. **Future Scope:**
     * Multi-warehouse network optimization
     * Advanced ML forecasting (DeepAR)
     * Automated supplier lead-time ROP
     * Android mobile app deployment
* **Closing Statement Banner:**
  * *"From prediction to allocation, our system helps retailers make practical inventory decisions."*
  * `Thank You | Questions?`
* **Visual Used:**
  * Structured 3-Card Visual Framework with distinctive theme borders and pill badges.
  * File: `reports/presentation_assets/slide6_impact_summary.png`
* **Data Source:** Project Roadmap & Hackathon Scope Definition
* **Estimated Speaking Time:** 60 seconds

### Speaker Notes (Slide 6)
> "To conclude, let's look at the operational impact, current boundaries, and future potential of our platform."
>
> "Business Impact: Retailers gain immediate clarity. Instead of guessing replenishment orders, stores receive fair, demand-backed stock that minimizes lost sales while protecting against inventory holding costs."
>
> "Current Limitations: Today, our baseline depends on historical point-of-sale transaction depth, models a single-warehouse tier, and requires available inventory to be user-provided."
>
> "Future Roadmap: We plan to expand into multi-echelon network optimization, integrate advanced probabilistic ML models like DeepAR, automate supplier lead-time reordering, and deploy our native Android mobile application for on-the-go warehouse operations."
>
> "From prediction to allocation, our system empowers retailers to make practical, data-driven inventory decisions."
>
> "Thank you, and we welcome your questions."
>
> *Sources:*  
> *Visual on this slide was generated with Microsoft Copilot.*

---

## Presentation Delivery Guide

| Slide # | Title | Primary Takeaway | Target Seconds |
| :---: | :--- | :--- | :---: |
| **1** | Title & Overview | Clear project purpose and supply chain context | 30s |
| **2** | The Problem | Scarcity gap: 1,200 demand vs 1,000 supply | 60s |
| **3** | How It Works | 6-stage end-to-end decision pipeline | 75s |
| **4** | Web Application | Interactive dashboard features & decision flow | 75s |
| **5** | Allocation Result | 417, 333, 250 distribution & mathematical invariants | 90s |
| **6** | Impact & Roadmap | Business ROI, realistic limitations, and future scope | 60s |
| **Total** | **Complete Review** | **Full Hackathon Presentation Pitch** | **390s (6m 30s)** |
