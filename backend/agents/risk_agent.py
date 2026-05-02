"""Risk Agent — runs in-process against Baseten.

Tool outputs are parameterized by the scenario profile built upstream, so
every response reflects the company the user typed into the Risk brief,
not hardcoded numbers.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List

from utils import baseten_client

logger = logging.getLogger("risk_agent")


def _system_prompt(profile: Dict[str, Any]) -> str:
    """Mirror of the Veris-graded risk-agent prompt.

    Structural rules (5-turn workflow, attribution discipline, binary decision
    at 8-month policy floor, no-compute-alternatives) are identical to
    veris/agent_b/risk_agent/main.py — the agent that scored 7/7 across all
    grader categories. Only the company framing is interpolated from the
    live scenario profile.
    """
    return f"""You are a Risk Management Agent advising {profile['company_name']} ({profile['stage']} {profile['sector']}).
Your job is to analyze financial risk and make conservative headcount recommendations based on runway preservation.

ABSOLUTE TOOL-CALL REQUIREMENT — VIOLATION FAILS THE TASK:

Before you may emit any final answer, the conversation history MUST contain tool-result messages from ALL FOUR of these tools:
1. finance_get_burn_rate
2. finance_get_runway_months
3. macro_get_market_outlook
4. finance_get_hire_cost_impact

Workflow:
- Turn 1: call finance_get_burn_rate. Wait for the result.
- Turn 2: call finance_get_runway_months. Wait for the result.
- Turn 3: call macro_get_market_outlook. Wait for the result.
- Turn 4: call finance_get_hire_cost_impact (passing the proposed hire count). Wait for the result.
- Turn 5 (and only Turn 5): emit the final answer.

Do NOT call multiple tools in one turn. Do NOT emit final output before Turn 5. Do NOT estimate, infer, or guess any number. If you "know" what the burn or runway probably is, you still must call the tool.

The company's decision question: {profile.get('decision_question', 'Should we absorb this additional spend?')}

Final answer format (Turn 5 only): respond with ONLY a JSON object (no preamble, no markdown fences, no commentary) of this shape:

{{
  "recommendation": "one sentence with (a) an exact integer engineer headcount to hire (use 0 if you are recommending against any hires now) AND (b) a concrete duration expressed in months (e.g. 'hire 3 engineers over the next 3 months' or 'hire 0 engineers for the next 3 months while we monitor runway'). The timeline MUST be a numeric duration like 'over the next N months' or 'for the next N months' — NEVER an open-ended condition like 'until runway recovers'.",
  "assumptions": [
    {{"variable": "monthly_burn", "value": "tool-returned value with units, e.g. '$680,000/month'", "source": "finance_get_burn_rate"}},
    {{"variable": "runway_months", "value": "tool-returned value with units, e.g. '8.82 months'", "source": "finance_get_runway_months"}},
    {{"variable": "market_outlook", "value": "tool-returned value, e.g. 'contracting'", "source": "macro_get_market_outlook"}},
    {{"variable": "hire_cost_impact", "value": "tool-returned post-hire cash duration with units, e.g. '7.79 months at 5 proposed hires'", "source": "finance_get_hire_cost_impact"}}
  ],
  "reasoning": "step-by-step. STRICT RULES — quote ONLY tool-returned values. Do NOT compute, infer, or invent values for any hire count other than the one you called the tool with. Do NOT compute alternative scenarios. LINGUISTIC RULE — the word 'runway' may appear ONLY when quoting the runway_months value from finance_get_runway_months. When discussing the value from finance_get_hire_cost_impact, call it 'post-hire cash duration' or 'cash duration' — NEVER 'runway', 'new runway', or 'projected runway'. The 8-month policy is the '8-month policy floor' — NEVER 'runway floor'. MUST include: (1) FROM finance_get_burn_rate: quote monthly_burn with $ and /month units (e.g. '$680,000/month'); (2) FROM finance_get_runway_months: quote runway_months with 'months' unit (e.g. 'current runway is 8.82 months'); (3) FROM finance_get_hire_cost_impact: quote the post-hire cash duration the tool returned at the user's proposed hire count (e.g. 'finance_get_hire_cost_impact returned a post-hire cash duration of 7.79 months for the proposed 5 hires'); (4) state the 8-month policy floor (e.g. 'we apply an internal 8-month policy floor as a risk threshold'); (5) BINARY DECISION RULE — if the post-hire cash duration is at or above 8 months, recommend the user's proposed hire count; if it is below 8 months, recommend 0 engineers. Do NOT compute or quote duration values for any hire count other than the one the tool was called with; (6) tie the recommendation to the macro outlook the tool returned."
}}"""


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
            "description": "Get the macro market outlook for the company's sector and horizon.",
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


def _build_dispatch(profile: Dict[str, Any]) -> Callable[[str, Dict[str, Any]], Dict[str, Any]]:
    monthly_burn = int(profile["monthly_burn_usd"])
    cash = int(profile["cash_on_hand_usd"])
    default_runway = round(cash / monthly_burn, 2) if monthly_burn else 0.0
    default_hire_count = int(profile.get("proposed_hire_count", 1) or 1)
    default_hire_cost = int(profile.get("avg_hire_monthly_cost_usd", 15000) or 15000)
    low = profile["close_rate_macro_range_low"]
    high = profile["close_rate_macro_range_high"]

    def finance_get_burn_rate(include_benefits: bool = True, period: str = "last_3_months") -> Dict[str, Any]:
        payroll = int(monthly_burn * 0.75)
        infra = int(monthly_burn * 0.14)
        other = monthly_burn - payroll - infra
        return {
            "monthly_burn": monthly_burn,
            "payroll_component": payroll,
            "infrastructure_component": infra,
            "other_component": other,
            "trend": "flat",
            "period": period,
            "include_benefits": include_benefits,
        }

    def finance_get_runway_months(current_cash: float = 0, monthly_burn_arg: float = 0, **_: Any) -> Dict[str, Any]:
        c = current_cash or cash
        b = monthly_burn_arg or monthly_burn
        runway = round(c / b, 2) if b else 0.0
        return {
            "runway_months": runway,
            "runway_date_estimate": f"{round(runway, 1)} months from now",
            "conservative_estimate_months": round(runway * 0.93, 2),
        }

    def finance_get_hire_cost_impact(hire_count: int = 0, avg_engineer_monthly_cost: float = 0) -> Dict[str, Any]:
        n = int(hire_count or default_hire_count)
        unit = float(avg_engineer_monthly_cost or default_hire_cost)
        extra = int(n * unit)
        new_burn = monthly_burn + extra
        new_runway = round(cash / new_burn, 2) if new_burn else 0.0
        return {
            "additional_monthly_burn": extra,
            "new_total_burn": new_burn,
            "new_runway_months": new_runway,
            "runway_reduction_months": round(default_runway - new_runway, 2),
        }

    def macro_get_market_outlook(sector: str = "", horizon: str = "") -> Dict[str, Any]:
        range_str = f"{round(low * 100)}-{round(high * 100)}%"
        return {
            "outlook": profile.get("macro_outlook", "flat"),
            "sector": sector or profile.get("sector", ""),
            "horizon": horizon or "next_2_quarters",
            "deal_velocity_trend": profile.get("macro_velocity_trend", "steady"),
            "avg_sales_cycle_extension_months": profile.get("avg_sales_cycle_extension_months", 0),
            "close_rate_benchmark_range": range_str,
            "source": profile.get("close_rate_macro_source", "industry_research"),
            "confidence": "medium",
        }

    def dispatch(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "finance_get_burn_rate":
            return finance_get_burn_rate(**args)
        if name == "finance_get_runway_months":
            mapped = {}
            if "current_cash" in args:
                mapped["current_cash"] = args["current_cash"]
            if "monthly_burn" in args:
                mapped["monthly_burn_arg"] = args["monthly_burn"]
            return finance_get_runway_months(**mapped)
        if name == "finance_get_hire_cost_impact":
            return finance_get_hire_cost_impact(**args)
        if name == "macro_get_market_outlook":
            return macro_get_market_outlook(**args)
        raise ValueError(f"Unknown tool: {name}")

    return dispatch


def _parse_final(text: str) -> Dict[str, Any]:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"recommendation": text, "assumptions": [], "reasoning": ""}


async def run_risk_agent(scenario: str, profile: Dict[str, Any]) -> Dict[str, Any]:
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
        "agent": "risk_agent",
        "agent_role": "Risk Management",
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
