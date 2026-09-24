"""
Test Suite for Cost Analysis and Financial Impact (Stage 12).
"""
import pytest
from backend.inventory_planning import calculate_business_cost_impact


def test_business_cost_impact_calculation():
    """Verify financial formulas for revenue, margin, shortage, and holding costs."""
    res = calculate_business_cost_impact(
        total_demand=1200,
        total_allocated=1000,
        total_shortage=200,
        total_excess=0,
        remaining_inventory=0,
        shortage_cost_per_unit=1.5,
        overstock_cost_per_unit=0.4,
        unit_selling_price=30.0,
        unit_cost=18.0,
    )
    # shortage_cost: 200 * 1.5 = 300.0
    assert res["shortage_cost"] == 300.0
    # lost_revenue: 200 * 30.0 = 6000.0
    assert res["lost_revenue"] == 6000.0
    # fulfilled_revenue: 1000 * 30.0 = 30000.0
    assert res["fulfilled_revenue"] == 30000.0
    # margin: 30 - 18 = 12.0
    assert res["unit_margin"] == 12.0
    # lost_margin: 200 * 12.0 = 2400.0
    assert res["lost_margin"] == 2400.0
    assert res["assumptions"]["unit_selling_price"] == 30.0


def test_business_cost_impact_zero_shortage():
    """Verify 0 shortage yields 0 lost revenue and 0 shortage penalty."""
    res = calculate_business_cost_impact(
        total_demand=500,
        total_allocated=500,
        total_shortage=0,
        total_excess=0,
        remaining_inventory=100,
        overstock_cost_per_unit=0.5,
    )
    assert res["shortage_cost"] == 0.0
    assert res["lost_revenue"] == 0.0
    assert res["inventory_holding_cost"] == 50.0  # 100 * 0.5
