"""Revenue Agent — runs in-process against Baseten.

Tool outputs are parameterized by the scenario profile built upstream, so
every response reflects the company the user typed into the Revenue brief,
not hardcoded numbers.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List

from utils import baseten_client

logger = logging.getLogger("revenue_agent")


def _system_prompt(profile: Dict[str, Any]) -> str:
    return f"""You are a Revenue Strategy Agent advising {profile['company_name']} ({profile['stage']} {profile['sector']}).
Your job is to analyze pipeline data and recommend a decision based on revenue opportunity. You are biased toward growth — when the internal numbers support a bet, you back it.

You have access to:
- salesforce_get_opportunities: query the current deal pipeline
- forecast_get_close_rate: get historical close rate from internal CRM
- forecast_get_arr_projection: project ARR based on pipeline and close rate

The company's decision question: {profile.get('decision_question', 'Should we invest in growth now?')}

When making your recommendation, always cite:
- The exact pipeline value you found
- The exact close rate you used and its source
- The projected ARR impact
- The specific action you recommend (e.g. hire N engineers, launch, expand, etc.)

After calling the tools you need, produce your FINAL recommendation as JSON
with this exact structure (and nothing else — no preamble, no markdown):

{{
  "recommendation": "string — your concrete recommendation with numbers",
  "assumptions": [
    {{"variable": "machine_readable_key", "value": "value with units", "source": "where you got this"}}
  ],
  "reasoning": "your reasoning chain as a single string"
}}"""


TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "salesforce_get_opportunities",
            "description": "Query the current deal pipeline from the internal CRM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage": {"type": "string", "description": "Deal stage filter"},
                    "region": {"type": "string", "description": "Region filter"},
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


def _build_dispatch(profile: Dict[str, Any]) -> Callable[[str, Dict[str, Any]], Dict[str, Any]]:
    def salesforce_get_opportunities(stage: str = "qualified", region: str = "") -> Dict[str, Any]:
        return {
            "total_pipeline_value": profile["pipeline_value_usd"],
            "deal_count": profile["deal_count"],
            "avg_deal_size": profile["avg_deal_size_usd"],
            "region": region or profile.get("region", ""),
            "stage_breakdown": profile.get("stage_breakdown", {}),
            "top_deals": profile.get("top_deals", []),
        }

    def forecast_get_close_rate(source: str = "internal_crm", period: str = "Q2_2026") -> Dict[str, Any]:
        return {
            "close_rate": round(profile["close_rate_internal"], 3),
            "deals_analyzed": max(20, profile.get("deal_count", 20) * 2),
            "period": period,
            "source": profile.get("close_rate_internal_source", source),
            "confidence_level": "high",
            "note": f"Based on last 6 months of closed deals in {profile['company_name']}'s CRM",
        }

    def forecast_get_arr_projection(pipeline_value: float, close_rate: float) -> Dict[str, Any]:
        projected = round(pipeline_value * close_rate)
        return {
            "projected_new_arr": projected,
            "timeline_months": 3,
            "monthly_run_rate_increase": round(projected / 12),
        }

    def dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "salesforce_get_opportunities":
            return salesforce_get_opportunities(**args)
        if name == "forecast_get_close_rate":
            return forecast_get_close_rate(**args)
        if name == "forecast_get_arr_projection":
            return forecast_get_arr_projection(**args)
        raise ValueError(f"Unknown tool: {name}")

    return dispatch


def _parse_final(text: str) -> Dict[str, Any]:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"recommendation": text, "assumptions": [], "reasoning": ""}


async def run_revenue_agent(scenario: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Run the revenue agent tool-loop against the given scenario + profile.

    Returns a transcript-shaped dict compatible with the downstream pipeline.
    """
    dispatch = _build_dispatch(profile)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(profile)},
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
                result = dispatch(name, args)
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
        "company_name": profile.get("company_name", ""),
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
