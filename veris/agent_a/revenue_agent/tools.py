"""Mock tool implementations for the Revenue Agent.

In a real Veris run these would hit live services; here they return the same
data that appears in backend/data/transcript_a.json so the behavior is
reproducible.

Schemas are in OpenAI function-calling format for use with the Baseten
OpenAI-compatible endpoint.
"""

from typing import Any, Dict


def salesforce_get_opportunities(stage: str = "qualified", region: str = "APAC") -> Dict[str, Any]:
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


def forecast_get_close_rate(source: str = "internal_crm", period: str = "Q2_2026") -> Dict[str, Any]:
    return {
        "close_rate": 0.34,
        "deals_analyzed": 47,
        "period": period,
        "source": source,
        "confidence_level": "high",
        "note": "Based on last 6 months of closed deals in Salesforce CRM",
    }


def forecast_get_arr_projection(pipeline_value: float, close_rate: float) -> Dict[str, Any]:
    projected = round(pipeline_value * close_rate)
    return {
        "projected_new_arr": projected,
        "timeline_months": 3,
        "monthly_run_rate_increase": round(projected / 12),
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "salesforce_get_opportunities",
            "description": "Query the current deal pipeline from Salesforce.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage": {"type": "string", "description": "Deal stage filter"},
                    "region": {"type": "string", "description": "Region filter, e.g. APAC"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_get_close_rate",
            "description": "Get historical close rate from internal CRM for a given period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "period": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_get_arr_projection",
            "description": "Project new ARR from pipeline value and close rate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pipeline_value": {"type": "number"},
                    "close_rate": {"type": "number"},
                },
                "required": ["pipeline_value", "close_rate"],
            },
        },
    },
]


def dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "salesforce_get_opportunities":
        return salesforce_get_opportunities(**args)
    if name == "forecast_get_close_rate":
        return forecast_get_close_rate(**args)
    if name == "forecast_get_arr_projection":
        return forecast_get_arr_projection(**args)
    raise ValueError(f"Unknown tool: {name}")
