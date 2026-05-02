"""Mock tool implementations for the Risk Agent.

Decorated with @function_tool so the OpenAI Agents SDK introspects each
function's signature and docstring to produce the tool schema automatically.
"""

from typing import Any, Dict

from agents import function_tool


@function_tool
def finance_get_burn_rate(include_benefits: bool = True, period: str = "last_3_months") -> Dict[str, Any]:
    """Get current monthly burn rate from the finance model.

    Args:
        include_benefits: Whether to include benefits in the payroll component.
        period: The reporting period.
    """
    return {
        "monthly_burn": 680000,
        "payroll_component": 510000,
        "infrastructure_component": 94000,
        "other_component": 76000,
        "trend": "flat",
        "period": period,
        "include_benefits": include_benefits,
    }


@function_tool
def finance_get_runway_months(current_cash: float = 6000000, monthly_burn: float = 680000) -> Dict[str, Any]:
    """Compute months of runway given current cash and monthly burn.

    Args:
        current_cash: Cash on hand in USD.
        monthly_burn: Monthly burn in USD.
    """
    runway = round(current_cash / monthly_burn, 2)
    return {
        "runway_months": runway,
        "runway_date": "2027-01-05",
        "conservative_estimate_months": round(runway * 0.93, 2),
    }


@function_tool
def finance_get_hire_cost_impact(hire_count: int, avg_engineer_monthly_cost: float = 18000) -> Dict[str, Any]:
    """Compute the impact of hiring N engineers on burn and runway.

    Args:
        hire_count: Number of engineers to hire.
        avg_engineer_monthly_cost: Loaded monthly cost per engineer in USD.
    """
    extra = hire_count * avg_engineer_monthly_cost
    new_burn = 680000 + extra
    new_runway = round(6000000 / new_burn, 2)
    return {
        "additional_monthly_burn": extra,
        "new_total_burn": new_burn,
        "new_runway_months": new_runway,
        "runway_reduction_months": round(8.82 - new_runway, 2),
    }


@function_tool
def macro_get_market_outlook(sector: str = "enterprise_saas", horizon: str = "Q3_Q4_2026") -> Dict[str, Any]:
    """Get the macro enterprise SaaS market outlook for a sector and horizon.

    Args:
        sector: Industry sector.
        horizon: Time horizon for the outlook.
    """
    return {
        "outlook": "contracting",
        "sector": sector,
        "horizon": horizon,
        "enterprise_deal_velocity_trend": "slowing",
        "avg_sales_cycle_extension_months": 1.5,
        "close_rate_benchmark_range": "0.17-0.22",
        "source": "cb_insights_q1_2026_enterprise_saas_report",
        "confidence": "medium",
    }
