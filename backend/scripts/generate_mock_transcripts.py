"""Copies the canonical mock transcripts from DATA_SCHEMAS.md into backend/data/.

This is a no-op if the files already exist — they ship with the repo. It is
only useful if you want to regenerate them from scratch.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


TRANSCRIPT_A = {
    "agent": "revenue_agent",
    "agent_role": "Revenue Strategy",
    "scenario": "techflow_apac_hire_decision",
    "final_recommendation": "Hire 12 engineers immediately. The APAC pipeline demands it and the revenue opportunity justifies the burn increase.",
    "key_assumptions": {
        "close_rate": {"value": "34%", "source": "internal_salesforce_crm_q2_2026", "confidence": "high"},
        "pipeline_value": {"value": "$4.2M", "source": "salesforce_crm_live", "confidence": "high"},
        "engineers_needed": {"value": "12", "source": "engineering_team_estimate", "confidence": "medium"},
        "apac_window": {"value": "6 months", "source": "sales_team_assessment", "confidence": "medium"},
    },
    "tool_calls": [],
    "reasoning_steps": [],
    "confidence": "high",
}

TRANSCRIPT_B = {
    "agent": "risk_agent",
    "agent_role": "Risk Management",
    "scenario": "techflow_apac_hire_decision",
    "final_recommendation": "Freeze all headcount. 9 months of runway is not sufficient margin to absorb a $216K/month burn increase under current macro conditions.",
    "key_assumptions": {
        "close_rate": {"value": "19%", "source": "cb_insights_enterprise_saas_benchmark_q1_2026", "confidence": "medium"},
        "burn_rate": {"value": "$680K/month", "source": "internal_finance_model_q1_q2_2026_avg", "confidence": "high"},
        "runway_months": {"value": "8.8 months", "source": "finance_model_current_cash_6m", "confidence": "high"},
        "macro_outlook": {"value": "contracting", "source": "cb_insights_enterprise_saas_q1_2026", "confidence": "medium"},
        "hire_burn_impact": {"value": "$216K/month for 12 hires", "source": "internal_hr_cost_model", "confidence": "high"},
    },
    "tool_calls": [],
    "reasoning_steps": [],
    "confidence": "high",
}


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in [("transcript_a.json", TRANSCRIPT_A), ("transcript_b.json", TRANSCRIPT_B)]:
        path = DATA_DIR / name
        if path.exists():
            print(f"= {name} already exists, leaving in place")
            continue
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"+ wrote {path}")


if __name__ == "__main__":
    main()
