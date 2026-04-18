"""Mock tool implementations for the Risk Agent.

Returns the same data that appears in backend/data/transcript_b.json so
agent behavior is reproducible.

Schemas are in OpenAI function-calling format for use with the Baseten
OpenAI-compatible endpoint.
"""

from typing import Any, Dict


def finance_get_burn_rate(include_benefits: bool = True, period: str = "last_3_months") -> Dict[str, Any]:
    return {
        "monthly_burn": 680000,
        "payroll_component": 510000,
        "infrastructure_component": 94000,
        "other_component": 76000,
        "trend": "flat",
        "period": period,
        "include_benefits": include_benefits,
    }


def finance_get_runway_months(current_cash: float = 6000000, monthly_burn: float = 680000) -> Dict[str, Any]:
    runway = round(current_cash / monthly_burn, 2)
    return {
        "runway_months": runway,
        "runway_date": "2027-01-05",
        "conservative_estimate_months": round(runway * 0.93, 2),
    }


def finance_get_hire_cost_impact(hire_count: int = 12, avg_engineer_monthly_cost: float = 18000) -> Dict[str, Any]:
    extra = hire_count * avg_engineer_monthly_cost
    new_burn = 680000 + extra
    new_runway = round(6000000 / new_burn, 2)
    return {
        "additional_monthly_burn": extra,
        "new_total_burn": new_burn,
        "new_runway_months": new_runway,
        "runway_reduction_months": round(8.82 - new_runway, 2),
    }


def macro_get_market_outlook(sector: str = "enterprise_saas", horizon: str = "Q3_Q4_2026") -> Dict[str, Any]:
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


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "finance_get_burn_rate",
            "description": "Get current monthly burn rate from the finance model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_benefits": {"type": "boolean"},
                    "period": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finance_get_runway_months",
            "description": "Compute months of runway given current cash and monthly burn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_cash": {"type": "number"},
                    "monthly_burn": {"type": "number"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finance_get_hire_cost_impact",
            "description": "Compute the impact of hiring N engineers on burn and runway.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hire_count": {"type": "integer"},
                    "avg_engineer_monthly_cost": {"type": "number"},
                },
                "required": ["hire_count"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "macro_get_market_outlook",
            "description": "Get the macro enterprise SaaS market outlook for a sector and horizon.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sector": {"type": "string"},
                    "horizon": {"type": "string"},
                },
            },
        },
    },
]


def dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "finance_get_burn_rate":
        return finance_get_burn_rate(**args)
    if name == "finance_get_runway_months":
        return finance_get_runway_months(**args)
    if name == "finance_get_hire_cost_impact":
        return finance_get_hire_cost_impact(**args)
    if name == "macro_get_market_outlook":
        return macro_get_market_outlook(**args)
    raise ValueError(f"Unknown tool: {name}")
