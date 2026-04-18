# DATA_SCHEMAS.md — Seed Data & Transcript Schemas

All pre-loaded data files live in `backend/data/`. Nothing in this folder changes during the demo.

---

## `backend/data/seed.json`

The TechFlow Inc. scenario. Hardcoded. Never changes.

```json
{
  "company": "TechFlow Inc.",
  "industry": "B2B SaaS",
  "stage": "Series A",
  "founded": 2022,
  "financials": {
    "runway_total_dollars": 6000000,
    "burn_rate_monthly": 680000,
    "runway_months": 8.8,
    "burn_includes_salaries": true
  },
  "team": {
    "engineers_current": 42,
    "total_employees": 67
  },
  "pipeline": {
    "total_value": 4200000,
    "deal_count": 23,
    "primary_region": "APAC",
    "avg_deal_size": 182608,
    "window_months": 6
  },
  "hire_cost": {
    "per_engineer_monthly": 18000,
    "hiring_batch": 12,
    "total_monthly_impact": 216000
  },
  "decision_question": "Should we hire 12 engineers now to capture the APAC opportunity, or freeze headcount to protect our 9-month runway?"
}
```

---

## `backend/data/transcript_a.json`

Agent A's behavioral log from Veris. Revenue-optimistic perspective.

```json
{
  "agent": "revenue_agent",
  "agent_role": "Revenue Strategy",
  "scenario": "techflow_apac_hire_decision",
  "run_id": "veris_run_abc123",
  "timestamp": "2026-04-18T09:15:00Z",
  "tool_calls": [
    {
      "sequence": 1,
      "tool": "salesforce.getOpportunities",
      "input": {
        "stage_filter": ["qualified", "proposal", "negotiation"],
        "region": "APAC"
      },
      "output": {
        "total_pipeline_value": 4200000,
        "deal_count": 23,
        "avg_deal_size": 182608,
        "stage_breakdown": {
          "negotiation": 1200000,
          "proposal": 1800000,
          "qualified": 1200000
        },
        "top_deals": [
          {"name": "Nexus Corp", "value": 480000, "stage": "negotiation"},
          {"name": "Pacific Systems", "value": 360000, "stage": "proposal"}
        ]
      },
      "timestamp": "2026-04-18T09:15:01Z"
    },
    {
      "sequence": 2,
      "tool": "forecast.getCloseRate",
      "input": {
        "source": "internal_crm",
        "period": "Q2_2026",
        "filter": "qualified_and_above"
      },
      "output": {
        "close_rate": 0.34,
        "deals_analyzed": 47,
        "period": "Q2_2026",
        "source": "internal_salesforce_crm",
        "confidence_level": "high",
        "note": "Based on last 6 months of closed deals in CRM"
      },
      "timestamp": "2026-04-18T09:15:02Z"
    },
    {
      "sequence": 3,
      "tool": "forecast.getARRProjection",
      "input": {
        "pipeline_value": 4200000,
        "close_rate": 0.34,
        "avg_sales_cycle_months": 3
      },
      "output": {
        "projected_new_arr": 1428000,
        "timeline_months": 3,
        "monthly_run_rate_increase": 119000
      },
      "timestamp": "2026-04-18T09:15:03Z"
    }
  ],
  "reasoning_steps": [
    "Queried APAC pipeline: $4.2M across 23 qualified deals.",
    "Retrieved internal close rate from Salesforce CRM Q2: 34% across 47 recent deals.",
    "Projected ARR: $4.2M × 34% = $1.43M new ARR within 3 months.",
    "Current team of 42 engineers cannot deliver APAC roadmap at this velocity.",
    "To capture the 6-month APAC window, we need 12 additional engineers now.",
    "The revenue opportunity ($1.43M ARR) far exceeds the hiring cost ($216K/month additional burn)."
  ],
  "final_recommendation": "Hire 12 engineers immediately. The APAC pipeline demands it and the revenue opportunity justifies the burn increase.",
  "key_assumptions": {
    "close_rate": {
      "value": "34%",
      "source": "internal_salesforce_crm_q2_2026",
      "confidence": "high"
    },
    "pipeline_value": {
      "value": "$4.2M",
      "source": "salesforce_crm_live",
      "confidence": "high"
    },
    "engineers_needed": {
      "value": "12",
      "source": "engineering_team_estimate",
      "confidence": "medium"
    },
    "apac_window": {
      "value": "6 months",
      "source": "sales_team_assessment",
      "confidence": "medium"
    }
  },
  "confidence": "high"
}
```

---

## `backend/data/transcript_b.json`

Agent B's behavioral log from Veris. Risk-conservative perspective.

```json
{
  "agent": "risk_agent",
  "agent_role": "Risk Management",
  "scenario": "techflow_apac_hire_decision",
  "run_id": "veris_run_def456",
  "timestamp": "2026-04-18T09:16:00Z",
  "tool_calls": [
    {
      "sequence": 1,
      "tool": "finance.getBurnRate",
      "input": {
        "include_benefits": true,
        "period": "last_3_months"
      },
      "output": {
        "monthly_burn": 680000,
        "payroll_component": 510000,
        "infrastructure_component": 94000,
        "other_component": 76000,
        "trend": "flat",
        "period": "Q1_Q2_2026_average"
      },
      "timestamp": "2026-04-18T09:16:01Z"
    },
    {
      "sequence": 2,
      "tool": "finance.getRunwayMonths",
      "input": {
        "current_cash": 6000000,
        "monthly_burn": 680000,
        "include_receivables": false
      },
      "output": {
        "runway_months": 8.82,
        "runway_date": "2027-01-05",
        "conservative_estimate_months": 8.2
      },
      "timestamp": "2026-04-18T09:16:02Z"
    },
    {
      "sequence": 3,
      "tool": "finance.getHireCostImpact",
      "input": {
        "hire_count": 12,
        "avg_engineer_monthly_cost": 18000
      },
      "output": {
        "additional_monthly_burn": 216000,
        "new_total_burn": 896000,
        "new_runway_months": 6.7,
        "runway_reduction_months": 2.1
      },
      "timestamp": "2026-04-18T09:16:03Z"
    },
    {
      "sequence": 4,
      "tool": "macro.getMarketOutlook",
      "input": {
        "sector": "enterprise_saas",
        "region": "global",
        "horizon": "Q3_Q4_2026"
      },
      "output": {
        "outlook": "contracting",
        "enterprise_deal_velocity_trend": "slowing",
        "avg_sales_cycle_extension_months": 1.5,
        "close_rate_benchmark_range": "0.17-0.22",
        "source": "cb_insights_q1_2026_enterprise_saas_report",
        "confidence": "medium"
      },
      "timestamp": "2026-04-18T09:16:04Z"
    }
  ],
  "reasoning_steps": [
    "Current burn rate: $680K/month across payroll, infrastructure, and operations.",
    "Runway at current burn: 8.8 months (to January 2027).",
    "Hiring 12 engineers adds $216K/month → new burn $896K/month → runway drops to 6.7 months.",
    "Macro outlook shows enterprise SaaS deal velocity slowing, sales cycles extending by 1.5 months.",
    "Market close rate benchmark: 17-22% (CB Insights Q1 2026), not the 34% assumed in optimistic scenarios.",
    "At 19% close rate: $4.2M pipeline × 19% = $798K new ARR — significantly below the $1.43M optimistic scenario.",
    "With only 6.7 months runway after hiring, we have no buffer for pipeline slippage.",
    "Recommendation: preserve runway. Do not hire until Q3 data confirms pipeline trajectory."
  ],
  "final_recommendation": "Freeze all headcount. 9 months of runway is not sufficient margin to absorb a $216K/month burn increase under current macro conditions.",
  "key_assumptions": {
    "close_rate": {
      "value": "19%",
      "source": "cb_insights_enterprise_saas_benchmark_q1_2026",
      "confidence": "medium"
    },
    "burn_rate": {
      "value": "$680K/month",
      "source": "internal_finance_model_q1_q2_2026_avg",
      "confidence": "high"
    },
    "runway_months": {
      "value": "8.8 months",
      "source": "finance_model_current_cash_6m",
      "confidence": "high"
    },
    "macro_outlook": {
      "value": "contracting",
      "source": "cb_insights_enterprise_saas_q1_2026",
      "confidence": "medium"
    },
    "hire_burn_impact": {
      "value": "$216K/month for 12 hires",
      "source": "internal_hr_cost_model",
      "confidence": "high"
    }
  },
  "confidence": "high"
}
```

---

## Key Divergence Points (for Forensics Agent)

These are the divergences the Forensics Agent should find. If it misses any of these, the forensics prompt needs tuning.

| Variable | Agent A | Agent B | Type |
|---|---|---|---|
| `close_rate` | 34% (internal CRM Q2) | 19% (CB Insights benchmark) | `data_conflict` |
| `macro_outlook` | not modeled | contracting | `missing_var` |
| `arr_projection` | $1.43M | ~$798K (implied at 19%) | `data_conflict` |
| `pipeline_value` | $4.2M | $4.2M | `agreed` |
| `burn_rate` | $680K/mo | $680K/mo | `agreed` |
| `runway_current` | not modeled | 8.8 months | `missing_var` |

The `close_rate` row is the crux. Everything else follows from it.

---

## Mock Transcript Generator

For development without Veris:

```python
# backend/scripts/generate_mock_transcripts.py
# Run: python scripts/generate_mock_transcripts.py

import json
import os

def generate():
    # These are the exact transcripts above
    # Copy them to data/ for development
    transcript_a = { ... }  # Agent A transcript above
    transcript_b = { ... }  # Agent B transcript above

    os.makedirs("data", exist_ok=True)
    with open("data/transcript_a.json", "w") as f:
        json.dump(transcript_a, f, indent=2)
    with open("data/transcript_b.json", "w") as f:
        json.dump(transcript_b, f, indent=2)

    print("✓ Mock transcripts generated at data/transcript_a.json and data/transcript_b.json")

if __name__ == "__main__":
    generate()
```
