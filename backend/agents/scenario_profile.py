"""Scenario profile builder.

Before the Revenue and Risk advisors run, we synthesize a single consistent
company profile from the user's two briefs. The advisor tools then read from
this profile, so every tool call reflects the scenario the user typed — not
hardcoded TechFlow numbers.

The profile deliberately splits close rate into an *internal* number
(Revenue trusts this) and a *macro benchmark range* (Risk trusts this). That
split is what creates the divergence downstream stages are tuned to detect.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from utils import baseten_client
from utils.json_utils import parse_claude_json

logger = logging.getLogger("scenario_profile")

PROFILE_PROMPT = """You are setting up a deterministic simulation of two AI advisors debating a startup business decision.

Below are two briefs describing the SAME company — one sent to the Revenue advisor, one to the Risk advisor. Extract every fact that is explicitly stated. For every field not stated, INVENT a plausible value that is internally consistent with the stated facts and with typical numbers for a company of that stage/sector/size.

IMPORTANT: The internal close rate (what the company's CRM shows) must be meaningfully more optimistic than the macro benchmark range (what industry reports show) — typically 1.3x to 2x higher. That gap is the whole point of the simulation.

Revenue advisor brief:
\"\"\"{scenario_a}\"\"\"

Risk advisor brief:
\"\"\"{scenario_b}\"\"\"

Return strict JSON with this exact shape:

{{
  "company_name": "string",
  "stage": "string e.g. 'Series A', 'Seed', 'Series B'",
  "sector": "string e.g. 'B2B SaaS', 'fintech payments', 'DevOps tooling'",
  "region": "string e.g. 'APAC', 'North America', 'EMEA', 'global'",
  "headcount_total": integer,
  "headcount_engineers": integer,
  "cash_on_hand_usd": integer,
  "monthly_burn_usd": integer,
  "runway_months": number,
  "pipeline_value_usd": integer,
  "deal_count": integer,
  "avg_deal_size_usd": integer,
  "stage_breakdown": {{"negotiation": integer, "proposal": integer, "qualified": integer}},
  "top_deals": [{{"name": "string", "value": integer, "stage": "string"}}],
  "close_rate_internal": number between 0 and 1,
  "close_rate_internal_source": "string e.g. 'internal_crm_q2_2026'",
  "close_rate_macro_range_low": number between 0 and 1,
  "close_rate_macro_range_high": number between 0 and 1,
  "close_rate_macro_source": "string e.g. 'cb_insights_enterprise_saas_q1_2026'",
  "avg_hire_monthly_cost_usd": integer,
  "proposed_hire_count": integer,
  "macro_outlook": "expanding | flat | contracting",
  "macro_velocity_trend": "accelerating | steady | slowing",
  "avg_sales_cycle_extension_months": number,
  "decision_question": "one-line summary of the decision being argued"
}}

Rules:
- top_deals should have 2 or 3 entries, each with a plausible invented company name.
- stage_breakdown values should roughly sum to pipeline_value_usd.
- runway_months should equal round(cash_on_hand_usd / monthly_burn_usd, 1).
- proposed_hire_count: if the briefs name a specific number, use it; otherwise pick something reasonable (1-20).
- If the briefs describe a non-hiring decision (pivot, pricing change, etc.), still populate hire fields with plausible defaults — downstream code reads them regardless.

Respond ONLY with valid JSON. No preamble, no markdown, no commentary."""


async def build_scenario_profile(scenario_a: str, scenario_b: str) -> Dict[str, Any]:
    prompt = PROFILE_PROMPT.format(scenario_a=scenario_a, scenario_b=scenario_b)
    raw = await baseten_client.complete(prompt, max_tokens=1500)
    profile = parse_claude_json(raw, stage="scenario_profile")

    required = [
        "company_name", "stage", "sector", "region",
        "cash_on_hand_usd", "monthly_burn_usd", "pipeline_value_usd",
        "close_rate_internal", "close_rate_macro_range_low", "close_rate_macro_range_high",
    ]
    missing = [k for k in required if k not in profile]
    if missing:
        raise RuntimeError(f"scenario_profile missing fields: {missing}")
    return profile
