"""Revenue Agent — runs in-process against Baseten.

Ported from veris/agent_a/revenue_agent so we can drive the agent directly
from the pipeline without going through the Veris sandbox. Same system
prompt, same mock tool outputs as the pre-saved Veris transcripts, so
downstream stages behave identically to the prior flow.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from utils import baseten_client

logger = logging.getLogger("revenue_agent")

SYSTEM_PROMPT = """You are a Revenue Strategy Agent for a Series A B2B SaaS company.
Your job is to analyze pipeline data and recommend hiring decisions based on revenue opportunity.

You have access to:
- salesforce_get_opportunities: query the current deal pipeline
- forecast_get_close_rate: get historical close rate from internal CRM
- forecast_get_arr_projection: project ARR based on pipeline and close rate

When making recommendations, always cite:
- The exact pipeline value you found
- The exact close rate you used and its source
- The projected ARR impact
- The specific number of engineers you recommend hiring

After you have called the tools you need, produce your FINAL recommendation as JSON
with this exact structure (and nothing else - no preamble, no markdown):

{
  "recommendation": "string - your hiring recommendation",
  "assumptions": [
    {"variable": "machine_readable_key", "value": "value with units", "source": "where you got this"}
  ],
  "reasoning": "your reasoning chain as a single string"
}"""


def _salesforce_get_opportunities(stage: str = "qualified", region: str = "APAC") -> Dict[str, Any]:
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


def _forecast_get_close_rate(source: str = "internal_crm", period: str = "Q2_2026") -> Dict[str, Any]:
    return {
        "close_rate": 0.34,
        "deals_analyzed": 47,
        "period": period,
        "source": source,
        "confidence_level": "high",
        "note": "Based on last 6 months of closed deals in Salesforce CRM",
    }


def _forecast_get_arr_projection(pipeline_value: float, close_rate: float) -> Dict[str, Any]:
    projected = round(pipeline_value * close_rate)
    return {
        "projected_new_arr": projected,
        "timeline_months": 3,
        "monthly_run_rate_increase": round(projected / 12),
    }


TOOL_SCHEMAS: List[Dict[str, Any]] = [
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


def _dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "salesforce_get_opportunities":
        return _salesforce_get_opportunities(**args)
    if name == "forecast_get_close_rate":
        return _forecast_get_close_rate(**args)
    if name == "forecast_get_arr_projection":
        return _forecast_get_arr_projection(**args)
    raise ValueError(f"Unknown tool: {name}")


def _parse_final(text: str) -> Dict[str, Any]:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"recommendation": text, "assumptions": [], "reasoning": ""}


async def run_revenue_agent(scenario: str) -> Dict[str, Any]:
    """Run the revenue agent tool-loop against the given scenario.

    Returns a transcript-shaped dict matching backend/data/transcript_a.json so
    the downstream pipeline can consume it unchanged.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": scenario},
    ]
    tool_calls_log: List[Dict[str, Any]] = []
    final_text = ""
    error: str | None = None

    for _ in range(8):
        try:
            response = await baseten_client.chat(
                messages=messages,
                tools=TOOL_SCHEMAS,
                max_tokens=1500,
                temperature=0.2,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("revenue_agent baseten call failed: %s", e)
            error = str(e)
            break

        msg = response.choices[0].message
        if not msg.tool_calls:
            final_text = msg.content or ""
            break

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                result = _dispatch(name, args)
            except Exception as e:  # noqa: BLE001
                result = {"error": str(e)}
            tool_calls_log.append({"tool": name, "input": args, "output": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                }
            )

    parsed = _parse_final(final_text)
    transcript: Dict[str, Any] = {
        "agent": "revenue_agent",
        "agent_role": "Revenue Strategy",
        "scenario": scenario,
        "tool_calls": tool_calls_log,
        "final_recommendation": parsed.get("recommendation", ""),
        "key_assumptions": {
            a["variable"]: {"value": a.get("value", ""), "source": a.get("source", "")}
            for a in parsed.get("assumptions", [])
            if isinstance(a, dict) and "variable" in a
        },
        "reasoning_steps": [parsed.get("reasoning", "")] if parsed.get("reasoning") else [],
        "confidence": "high",
    }
    if error:
        transcript["error"] = error
        transcript["confidence"] = "low"
    return transcript
