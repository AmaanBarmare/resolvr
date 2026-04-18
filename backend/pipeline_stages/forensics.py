import json
import os
from typing import Dict

from exceptions import PipelineError
from models import ForensicsOutput
from prompts import FORENSICS_PROMPT
from utils import baseten_client
from utils.json_utils import parse_claude_json

FORENSICS_MAX_TOKENS = int(os.getenv("FORENSICS_MAX_TOKENS", "2000"))


# Mock — exactly the "good output" from DATA_SCHEMAS.md / PIPELINE.md
MOCK_FORENSICS = {
    "assumption_table": [
        {
            "variable": "close_rate",
            "agent_a_value": "34%",
            "agent_a_source": "internal_salesforce_crm_q2_2026",
            "agent_b_value": "19%",
            "agent_b_source": "cb_insights_enterprise_saas_benchmark_q1_2026",
            "divergence_type": "data_conflict",
            "is_crux": True,
        },
        {
            "variable": "pipeline_value",
            "agent_a_value": "$4.2M",
            "agent_a_source": "salesforce_crm_live",
            "agent_b_value": "$4.2M",
            "agent_b_source": "salesforce_crm_live",
            "divergence_type": "agreed",
            "is_crux": False,
        },
        {
            "variable": "macro_outlook",
            "agent_a_value": "not modeled",
            "agent_a_source": "n/a",
            "agent_b_value": "contracting",
            "agent_b_source": "cb_insights_enterprise_saas_q1_2026",
            "divergence_type": "missing_var",
            "is_crux": False,
        },
        {
            "variable": "runway_months",
            "agent_a_value": "not modeled",
            "agent_a_source": "n/a",
            "agent_b_value": "8.8 months",
            "agent_b_source": "finance_model_current_cash_6m",
            "divergence_type": "missing_var",
            "is_crux": False,
        },
        {
            "variable": "arr_projection",
            "agent_a_value": "$1.43M",
            "agent_a_source": "internal_arr_projection_34pct",
            "agent_b_value": "$798K (implied at 19%)",
            "agent_b_source": "implied_from_benchmark_close_rate",
            "divergence_type": "data_conflict",
            "is_crux": False,
        },
    ],
    "divergence_type": "data_conflict",
    "finding": (
        "Agents split at close_rate: Agent A used 34% (internal CRM Q2) vs "
        "Agent B 19% (CB Insights macro benchmark). Agent A's hiring case "
        "collapses if close rate drops below 26%."
    ),
    "crux_variable": "close_rate",
}


async def run_forensics(transcripts: Dict[str, dict]) -> ForensicsOutput:
    if os.getenv("USE_MOCK_PIPELINE", "").lower() == "true":
        return ForensicsOutput(**MOCK_FORENSICS)

    prompt = FORENSICS_PROMPT.format(
        transcript_a=json.dumps(transcripts["agent_a"], indent=2),
        transcript_b=json.dumps(transcripts["agent_b"], indent=2),
    )

    raw = await baseten_client.complete(prompt, max_tokens=FORENSICS_MAX_TOKENS)
    parsed = parse_claude_json(raw, stage="forensics")

    if "assumption_table" not in parsed or "finding" not in parsed:
        raise PipelineError(
            stage="forensics",
            message="Forensics output missing required fields",
        )
    if not any(row.get("is_crux") for row in parsed["assumption_table"]):
        # Force the first row to be crux if model forgot
        parsed["assumption_table"][0]["is_crux"] = True

    return ForensicsOutput(**parsed)
