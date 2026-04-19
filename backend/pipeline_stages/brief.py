import os
import re

from models import (
    AuditEntry,
    BriefOutput,
    ForensicsOutput,
    GroundingOutput,
    SimulationOutput,
)
from prompts import BRIEF_PROMPT
from utils import baseten_client
from utils.json_utils import parse_claude_json

BRIEF_MAX_TOKENS = int(os.getenv("BRIEF_MAX_TOKENS", "2500"))

# The sample cases all use a 6-month decision window. Normalize any other
# horizon the LLM drifts into so the verdict stays aligned with the case.
TRIGGER_WINDOW_MONTHS = int(os.getenv("TRIGGER_WINDOW_MONTHS", "6"))

_WITHIN_MONTHS_RE = re.compile(
    r"within\s+\d+(?:\.\d+)?\s*(?:-\s*\d+(?:\.\d+)?\s*)?months?",
    flags=re.IGNORECASE,
)
_IN_THE_NEXT_MONTHS_RE = re.compile(
    r"in\s+the\s+next\s+\d+(?:\.\d+)?\s*months?",
    flags=re.IGNORECASE,
)


def _normalize_window(text: str) -> str:
    if not text:
        return text
    target = f"within {TRIGGER_WINDOW_MONTHS} months"
    text = _WITHIN_MONTHS_RE.sub(target, text)
    text = _IN_THE_NEXT_MONTHS_RE.sub(target, text)
    return text


MOCK_BRIEF = {
    "headline": "On the question of APAC headcount",
    "context": (
        "TechFlow's Revenue and Risk agents both analyzed the APAC hiring decision "
        "and reached opposite conclusions based on different close-rate assumptions."
    ),
    "divergence_finding": (
        "The disagreement reduces to one number: close rate. Agent A used 34% "
        "(internal CRM Q2) - 1.7x above the Gartner market median of 17-22%."
    ),
    "recommended_decision": (
        "Hire 4 engineers now. Expand to 12 if Q3 pipeline closes above $3M ARR."
    ),
    "rationale": (
        "Agent A's hiring case depends on a 34% close rate, which Gartner benchmarks "
        "as an outlier at 1.7x the market median of 17-22%. Until Q3 data validates "
        "this assumption, full-scale hiring is a $216K/month bet on an unverified "
        "number. The hybrid path preserves ~8 months of runway while maintaining "
        "70% of pipeline execution capacity."
    ),
    "dissenting_opinion": (
        "Agent B's position: even 4 hires reduces runway from 8.8 to 7.8 months. "
        "If the macro enterprise SaaS slowdown accelerates beyond current benchmarks, "
        "the Q3 trigger threshold may be unreachable, and the company will have "
        "burned $72K per hire with no expansion path. Full freeze until Q3 data "
        "confirms Agent A's close rate is the cleaner risk-preserving move."
    ),
    "trigger_conditions": [
        "Expand to 12 engineers if Q3 pipeline closes above $3M ARR",
        "Freeze further expansion if monthly burn exceeds $900K for 2 consecutive months",
        "Cancel APAC initiative if enterprise SaaS macro index drops more than 15% vs Q1 2026 baseline",
    ],
    "audit_log": [
        {
            "claim": "Enterprise SaaS close-rate market median 17-22%",
            "source_url": "https://gartner.com/en/sales/insights/saas-sales-benchmarks",
            "source_name": "Gartner Enterprise SaaS Sales Benchmarks 2026",
        },
        {
            "claim": "APAC enterprise software market growing 18% YoY",
            "source_url": "https://idc.com/getdoc.jsp?containerId=AP49823",
            "source_name": "IDC APAC Enterprise Software Market Forecast 2026",
        },
        {
            "claim": "Enterprise SaaS deal velocity slowing Q3/Q4 2026",
            "source_url": "https://cbinsights.com/research/enterprise-saas-q1-2026",
            "source_name": "CB Insights Enterprise SaaS Report Q1 2026",
        },
    ],
}


def _summary(path) -> str:
    return f"{path.name} - {path.description} | success: {path.success_condition} | failure: {path.failure_condition}"


def _grounding_block(g: GroundingOutput) -> str:
    return "\n".join(
        f"- {ga.variable}: benchmark={ga.market_benchmark}, verdict={ga.verdict}, "
        f"source={ga.source_name} ({ga.source_url})"
        for ga in g.grounded_assumptions
    )


async def run_brief(
    forensics: ForensicsOutput,
    grounding: GroundingOutput,
    simulation: SimulationOutput,
    seed: dict,
) -> BriefOutput:
    if os.getenv("USE_MOCK_PIPELINE", "").lower() == "true":
        return BriefOutput(
            headline=MOCK_BRIEF["headline"],
            context=MOCK_BRIEF["context"],
            divergence_finding=MOCK_BRIEF["divergence_finding"],
            recommended_decision=MOCK_BRIEF["recommended_decision"],
            rationale=MOCK_BRIEF["rationale"],
            dissenting_opinion=MOCK_BRIEF["dissenting_opinion"],
            trigger_conditions=MOCK_BRIEF["trigger_conditions"],
            audit_log=[AuditEntry(**e) for e in MOCK_BRIEF["audit_log"]],
        )

    prompt = BRIEF_PROMPT.format(
        company_name=seed.get("company", "The Company"),
        decision_question=seed.get("decision_question", ""),
        finding=forensics.finding,
        grounding_summary=_grounding_block(grounding),
        path_a_summary=_summary(simulation.path_a),
        path_b_summary=_summary(simulation.path_b),
        hybrid_summary=_summary(simulation.hybrid),
    )
    raw = await baseten_client.complete(prompt, max_tokens=BRIEF_MAX_TOKENS)
    parsed = parse_claude_json(raw, stage="brief")

    # Enforce the case's decision window on any time-bound trigger.
    if isinstance(parsed.get("recommended_decision"), str):
        parsed["recommended_decision"] = _normalize_window(parsed["recommended_decision"])
    if isinstance(parsed.get("rationale"), str):
        parsed["rationale"] = _normalize_window(parsed["rationale"])
    if isinstance(parsed.get("trigger_conditions"), list):
        parsed["trigger_conditions"] = [
            _normalize_window(t) if isinstance(t, str) else t
            for t in parsed["trigger_conditions"]
        ]

    return BriefOutput(**parsed)
