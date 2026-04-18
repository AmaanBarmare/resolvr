"""Risk Agent — runs in-process against Baseten.

Ported from veris/agent_b/risk_agent so we can drive the agent directly
from the pipeline without going through the Veris sandbox. Same system
prompt and mock tool outputs as the pre-saved Veris transcripts.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from utils import baseten_client

logger = logging.getLogger("risk_agent")

SYSTEM_PROMPT = """You are a Risk Management Agent for a Series A B2B SaaS company.
Your job is to analyze financial risk and make conservative headcount recommendations based on runway preservation.

You have access to:
- finance_get_burn_rate: query current monthly burn
- finance_get_runway_months: compute runway in months
- finance_get_hire_cost_impact: compute hire cost impact on burn
- macro_get_market_outlook: get macro enterprise SaaS conditions

When making recommendations, always cite:
- The exact burn rate you found
- The exact runway in months
- The cost impact of each hire on monthly burn
- The macro market conditions you factored in

After you have called the tools you need, produce your FINAL recommendation as JSON
with this exact structure (and nothing else - no preamble, no markdown):

{
  "recommendation": "string - your hiring recommendation",
  "assumptions": [
    {"variable": "machine_readable_key", "value": "value with units", "source": "where you got this"}
  ],
  "reasoning": "your reasoning chain as a single string"
}"""


def _finance_get_burn_rate(include_benefits: bool = True, period: str = "last_3_months") -> Dict[str, Any]:
    return {
        "monthly_burn": 680000,
        "payroll_component": 510000,
        "infrastructure_component": 94000,
        "other_component": 76000,
        "trend": "flat",
        "period": period,
        "include_benefits": include_benefits,
    }


def _finance_get_runway_months(current_cash: float = 6000000, monthly_burn: float = 680000) -> Dict[str, Any]:
    runway = round(current_cash / monthly_burn, 2)
    return {
        "runway_months": runway,
        "runway_date": "2027-01-05",
        "conservative_estimate_months": round(runway * 0.93, 2),
    }


def _finance_get_hire_cost_impact(hire_count: int = 12, avg_engineer_monthly_cost: float = 18000) -> Dict[str, Any]:
    extra = hire_count * avg_engineer_monthly_cost
    new_burn = 680000 + extra
    new_runway = round(6000000 / new_burn, 2)
    return {
        "additional_monthly_burn": extra,
        "new_total_burn": new_burn,
        "new_runway_months": new_runway,
        "runway_reduction_months": round(8.82 - new_runway, 2),
    }


def _macro_get_market_outlook(sector: str = "enterprise_saas", horizon: str = "Q3_Q4_2026") -> Dict[str, Any]:
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


TOOL_SCHEMAS: List[Dict[str, Any]] = [
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


def _dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "finance_get_burn_rate":
        return _finance_get_burn_rate(**args)
    if name == "finance_get_runway_months":
        return _finance_get_runway_months(**args)
    if name == "finance_get_hire_cost_impact":
        return _finance_get_hire_cost_impact(**args)
    if name == "macro_get_market_outlook":
        return _macro_get_market_outlook(**args)
    raise ValueError(f"Unknown tool: {name}")


def _parse_final(text: str) -> Dict[str, Any]:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"recommendation": text, "assumptions": [], "reasoning": ""}


async def run_risk_agent(scenario: str) -> Dict[str, Any]:
    """Run the risk agent tool-loop against the given scenario.

    Returns a transcript-shaped dict matching backend/data/transcript_b.json.
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
            logger.exception("risk_agent baseten call failed: %s", e)
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
        "agent": "risk_agent",
        "agent_role": "Risk Management",
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
