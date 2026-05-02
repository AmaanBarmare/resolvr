"""Mock tool implementations for the Revenue Agent.

Decorated with @function_tool so the OpenAI Agents SDK introspects each
function's signature and docstring to produce the tool schema automatically.
"""

from typing import Any, Dict

from agents import function_tool


@function_tool
def salesforce_get_opportunities(stage: str = "qualified", region: str = "APAC") -> Dict[str, Any]:
    """Query the current deal pipeline from Salesforce.

    Args:
        stage: Deal stage filter (e.g. qualified, negotiation).
        region: Region filter, e.g. APAC.
    """
    return {
        "total_pipeline_value": 4200000,
        "deal_count": 23,
        "avg_deal_size": 182608,
        "region": region,
        "stage_breakdown": {
            "negotiation": 1200000,
            "proposal": 1800000,
            "qualified": 1200000,
        },
        "top_deals": [
            {"name": "Nexus Corp", "value": 480000, "stage": "negotiation"},
            {"name": "Pacific Systems", "value": 360000, "stage": "proposal"},
        ],
    }


@function_tool
def forecast_get_close_rate(source: str = "internal_crm", period: str = "Q2_2026") -> Dict[str, Any]:
    """Get historical close rate from internal CRM for a given period.

    Args:
        source: Which CRM to read from.
        period: Reporting period.
    """
    return {
        "close_rate": 0.34,
        "deals_analyzed": 47,
        "period": period,
        "source": source,
        "confidence_level": "high",
        "note": "Based on last 6 months of closed deals in Salesforce CRM",
    }


@function_tool
def forecast_get_arr_projection(pipeline_value: float, close_rate: float) -> Dict[str, Any]:
    """Project new ARR from pipeline value and close rate.

    Args:
        pipeline_value: Total pipeline value in USD.
        close_rate: Expected close rate as a decimal (e.g. 0.34 for 34%).
    """
    projected = round(pipeline_value * close_rate)
    return {
        "projected_new_arr": projected,
        "timeline_months": 3,
        "monthly_run_rate_increase": round(projected / 12),
    }
