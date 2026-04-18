# AGENTS.md — Building Agent A and Agent B

The two agents are Python programs that run inside Veris. Each agent takes a scenario, calls mock tools, and produces a structured recommendation with named assumptions.

---

## What Agents Need to Do

Each agent must:
1. Receive the TechFlow scenario as a prompt
2. Call its mock tools (Salesforce for A, finance model for B)
3. Reason about the tool outputs
4. Return a structured recommendation with **every number explicitly named and sourced**

The named numbers are critical — the Forensics Agent reads the Veris transcript and extracts them. If the agent just says "growth looks good" without citing specific numbers, forensics produces nothing useful.

---

## Agent A — Revenue Agent

**Role:** Optimize for pipeline velocity and growth. Bullish on APAC opportunity.

**Tools it calls:**
- `salesforce.getOpportunities` → pipeline value, deal count, stage breakdown
- `forecast.getCloseRate` → historical close rate from internal CRM
- `forecast.getARRProjection` → projected ARR if deals close

**System prompt:**

```
You are a Revenue Strategy Agent for a Series A B2B SaaS company.
Your job is to analyze pipeline data and recommend hiring decisions
based on revenue opportunity.

You have access to:
- salesforce: to query the current deal pipeline
- forecast: to get close rates and ARR projections

When making recommendations, always cite:
- The exact pipeline value you found
- The exact close rate you used and its source
- The projected ARR impact
- The specific number of engineers you recommend hiring

Output your final recommendation as JSON with this structure:
{
  "recommendation": "string — your hiring recommendation",
  "assumptions": [
    {
      "variable": "machine_readable_key",
      "value": "value with units",
      "source": "where you got this"
    }
  ],
  "reasoning": "your reasoning chain"
}
```

**File:** `veris/agent_a/revenue_agent/main.py`

```python
import os
import json
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_ID = os.getenv("BASETEN_MODEL_ID")

SYSTEM_PROMPT = """You are a Revenue Strategy Agent...."""  # full prompt above

TOOLS = [
    {
        "name": "salesforce_get_opportunities",
        "description": "Get current deal pipeline from Salesforce",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "Deal stage filter"}
            }
        }
    },
    {
        "name": "forecast_get_close_rate",
        "description": "Get historical close rate from internal CRM",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "period": {"type": "string"}
            }
        }
    },
    {
        "name": "forecast_get_arr_projection",
        "description": "Project ARR based on pipeline and close rate",
        "input_schema": {
            "type": "object",
            "properties": {
                "pipeline_value": {"type": "number"},
                "close_rate": {"type": "number"}
            }
        }
    }
]

@app.post("/")
async def handle_message(request: Request):
    body = await request.json()
    user_message = body.get("message", "")

    # Call Claude via Baseten with tool use
    response = await call_claude_with_tools(user_message)
    return {"response": response}


async def call_claude_with_tools(scenario: str) -> str:
    # Baseten inference call
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://model-{BASETEN_MODEL_ID}.api.baseten.co/production/predict",
            headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
            json={
                "messages": [{"role": "user", "content": scenario}],
                "system": SYSTEM_PROMPT,
                "tools": TOOLS,
                "max_tokens": 2000
            }
        )
    # Handle tool use loop
    # Return final JSON recommendation
    ...
```

---

## Agent B — Risk Agent

**Role:** Optimize for survival. Protect runway. Conservative on macro.

**Tools it calls:**
- `finance.getBurnRate` → current monthly burn
- `finance.getRunwayMonths` → months of runway at current burn
- `finance.getHireCostImpact` → how much each hire adds to monthly burn
- `macro.getMarketOutlook` → macro enterprise SaaS conditions

**System prompt:**

```
You are a Risk Management Agent for a Series A B2B SaaS company.
Your job is to analyze financial risk and make conservative
headcount recommendations based on runway preservation.

You have access to:
- finance: to query burn rate, runway, and cost projections
- macro: to get market condition indicators

When making recommendations, always cite:
- The exact burn rate you found
- The exact runway in months
- The cost impact of each hire on monthly burn
- The macro market conditions you factored in

Output your final recommendation as JSON with this structure:
{
  "recommendation": "string — your hiring recommendation",
  "assumptions": [
    {
      "variable": "machine_readable_key",
      "value": "value with units",
      "source": "where you got this"
    }
  ],
  "reasoning": "your reasoning chain"
}
```

---

## Veris Configuration

### Agent A — `veris/agent_a/veris.yaml`

```yaml
services:
  - name: salesforce
    dns_aliases:
      - api.salesforce.com
      - api.salesforce.mock

  - name: forecast-api
    dns_aliases:
      - forecast.internal
      - forecast.techflow.mock

actor:
  channels:
    - type: http
      url: http://localhost:8001
      method: POST
      headers:
        Content-Type: application/json
      request:
        message_field: message
        session_field: session_id
      response:
        type: json
        message_field: response

agent:
  code_path: /agent
  entry_point: python -m revenue_agent.main
  port: 8001

environment:
  BASETEN_API_KEY: ""         # set via: veris env vars set BASETEN_API_KEY=xxx --secret
  BASETEN_MODEL_ID: ""
```

### Agent B — `veris/agent_b/veris.yaml`

```yaml
services:
  - name: finance-model
    dns_aliases:
      - finance.internal
      - finance.techflow.mock

  - name: macro-api
    dns_aliases:
      - macro.internal
      - macro.research.mock

actor:
  channels:
    - type: http
      url: http://localhost:8002
      method: POST
      headers:
        Content-Type: application/json
      request:
        message_field: message
        session_field: session_id
      response:
        type: json
        message_field: response

agent:
  code_path: /agent
  entry_point: python -m risk_agent.main
  port: 8002

environment:
  BASETEN_API_KEY: ""
  BASETEN_MODEL_ID: ""
```

### Agent A — `veris/agent_a/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /agent
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY revenue_agent/ revenue_agent/
CMD ["python", "-m", "revenue_agent.main"]
```

### Agent B — `veris/agent_b/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /agent
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY risk_agent/ risk_agent/
CMD ["python", "-m", "risk_agent.main"]
```

---

## What a Good Transcript Looks Like

After running Veris, the transcript JSON for Agent A should look like this. If it doesn't contain named numbers with sources, the forensics agent will fail.

```json
{
  "agent": "revenue_agent",
  "scenario": "techflow_hire_decision",
  "tool_calls": [
    {
      "tool": "salesforce.getOpportunities",
      "input": {"stage": "qualified"},
      "output": {
        "pipeline_value": 4200000,
        "deal_count": 23,
        "avg_deal_size": 182608,
        "top_region": "APAC"
      }
    },
    {
      "tool": "forecast.getCloseRate",
      "input": {"source": "internal_crm", "period": "Q2_2026"},
      "output": {
        "close_rate": 0.34,
        "period": "Q2_2026",
        "source": "internal_salesforce_crm",
        "confidence": "high"
      }
    },
    {
      "tool": "forecast.getARRProjection",
      "input": {"pipeline_value": 4200000, "close_rate": 0.34},
      "output": {
        "projected_arr": 1428000,
        "timeline_months": 6
      }
    }
  ],
  "reasoning_steps": [
    "Current APAC pipeline: $4.2M across 23 deals.",
    "Internal CRM shows 34% close rate for Q2 2026.",
    "At 34% close rate: $4.2M × 0.34 = $1.43M new ARR.",
    "To deliver APAC roadmap in 6 months, need 12 engineers.",
    "Revenue justifies headcount investment."
  ],
  "final_recommendation": "Hire 12 engineers immediately. Pipeline velocity demands it.",
  "key_assumptions": {
    "close_rate": {"value": "34%", "source": "internal_crm_q2"},
    "pipeline_value": {"value": "$4.2M", "source": "salesforce"},
    "engineers_needed": {"value": "12", "source": "engineering_estimate"}
  }
}
```

---

## Mock Transcripts for Development

If Veris isn't ready, generate mock transcripts for local development:

```bash
cd backend
python scripts/generate_mock_transcripts.py
# Creates backend/data/transcript_a.json and transcript_b.json
```

The mock transcripts are realistic enough for the forensics agent to work on. Use them during development, then replace with real Veris transcripts before the demo.
