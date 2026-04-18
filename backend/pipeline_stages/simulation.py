import json
import os

from models import ForensicsOutput, GroundingOutput, OutcomePath, SimulationOutput
from prompts import SIMULATION_PROMPT
from utils import baseten_client
from utils.json_utils import parse_claude_json

SIMULATION_MAX_TOKENS = int(os.getenv("SIMULATION_MAX_TOKENS", "1500"))


MOCK_SIMULATION = {
    "path_a": {
        "name": "Hire 12 Engineers",
        "description": (
            "Follow Agent A's revenue-driven plan. Hire all 12 engineers immediately "
            "and commit fully to the APAC pipeline within the 6-month window."
        ),
        "success_condition": "IF APAC pipeline closes above $2.8M ARR by Q3 2026",
        "failure_condition": "IF close rate stays near the 19% market benchmark - runway drops to 6.7 months with no buffer",
        "recommended": False,
    },
    "path_b": {
        "name": "Freeze Headcount",
        "description": (
            "Follow Agent B's risk-preserving plan. Hold team at 42 engineers and let "
            "the APAC window compress while preserving the full 8.8 months of runway."
        ),
        "success_condition": "IF macro SaaS conditions contract further in Q3/Q4 2026",
        "failure_condition": "IF APAC window closes and pipeline velocity drops 30%+",
        "recommended": False,
    },
    "hybrid": {
        "name": "Hire 4 + Trigger",
        "description": (
            "Hire 4 engineers now to maintain APAC delivery velocity, then expand to "
            "12 if Q3 pipeline closes above $3M ARR. Preserves ~8 months of runway while "
            "keeping 70% of pipeline execution capacity."
        ),
        "success_condition": "IF Q3 pipeline closes above $3M ARR - expand to 12",
        "failure_condition": "IF macro index drops >15% vs Q1 2026 baseline - freeze and reassess",
        "recommended": True,
    },
}


def _summarize_forensics(f: ForensicsOutput) -> str:
    rows = "\n".join(
        f"- {r.variable}: A={r.agent_a_value} ({r.agent_a_source}) | "
        f"B={r.agent_b_value} ({r.agent_b_source}) | {r.divergence_type}"
        + (" [CRUX]" if r.is_crux else "")
        for r in f.assumption_table
    )
    return f"Finding: {f.finding}\nAssumptions:\n{rows}"


def _summarize_grounding(g: GroundingOutput) -> str:
    return "\n".join(
        f"- {ga.variable}: benchmark={ga.market_benchmark}, verdict={ga.verdict}, "
        f"note={ga.note}"
        for ga in g.grounded_assumptions
    )


async def run_simulation(
    forensics: ForensicsOutput,
    grounding: GroundingOutput,
    seed: dict,
) -> SimulationOutput:
    if os.getenv("USE_MOCK_PIPELINE", "").lower() == "true":
        return SimulationOutput(
            path_a=OutcomePath(**MOCK_SIMULATION["path_a"]),
            path_b=OutcomePath(**MOCK_SIMULATION["path_b"]),
            hybrid=OutcomePath(**MOCK_SIMULATION["hybrid"]),
        )

    prompt = SIMULATION_PROMPT.format(
        seed_data=json.dumps(seed, indent=2),
        forensics_summary=_summarize_forensics(forensics),
        grounding_summary=_summarize_grounding(grounding),
        crux_variable=forensics.crux_variable,
    )
    raw = await baseten_client.complete(prompt, max_tokens=SIMULATION_MAX_TOKENS)
    parsed = parse_claude_json(raw, stage="simulation")
    return SimulationOutput(**parsed)
