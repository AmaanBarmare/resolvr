# API.md — Backend API Reference

Base URL: `http://localhost:8000`

---

## Endpoints

### `GET /health`

Health check. Returns 200 if the backend is running and transcripts are loaded.

**Response:**
```json
{
  "status": "ok",
  "transcripts_loaded": true,
  "seed_loaded": true
}
```

---

### `GET /api/run`

Runs the full arbitration pipeline. Returns a Server-Sent Events (SSE) stream.

**Headers required:**
```
Accept: text/event-stream
Cache-Control: no-cache
```

**SSE Event Format:**

Every event is a JSON object on a `data:` line, followed by two newlines.

```
data: <json>\n\n
```

**Event types:**

```typescript
// Loading event — sent at start of each stage
{
  stage: number | "done",
  status: "loading",
  message: string    // human-readable description
}

// Complete event — sent when a stage finishes
{
  stage: number,
  status: "complete",
  data: StageOutput  // see schemas below
}

// Final event — pipeline complete
{
  stage: "done",
  status: "complete"
}

// Error event — pipeline failed
{
  stage: number | string,
  status: "error",
  message: string
}
```

**Stage 1 complete — `data` schema:**
```typescript
{
  agent_a: {
    recommendation: string,       // "Hire 12 engineers now"
    assumptions: Array<{
      variable: string,           // "close_rate"
      value: string,              // "34%"
      source: string              // "internal_crm_q2"
    }>,
    source: string                // "transcript_a.json"
  },
  agent_b: {
    recommendation: string,
    assumptions: Array<{...}>,
    source: string
  }
}
```

**Stage 2 complete — `data` schema:**
```typescript
{
  assumption_table: Array<{
    variable: string,             // "close_rate"
    agent_a_value: string,        // "34%"
    agent_a_source: string,       // "internal_crm_q2"
    agent_b_value: string,        // "19%"
    agent_b_source: string,       // "macro_benchmark"
    divergence_type: "data_conflict" | "missing_var" | "horizon_mismatch" | "agreed",
    is_crux: boolean
  }>,
  divergence_type: string,
  finding: string,                // one-sentence divergence statement
  crux_variable: string           // "close_rate"
}
```

**Stage 3 complete — `data` schema:**
```typescript
{
  grounded_assumptions: Array<{
    variable: string,
    agent_a_value: string,
    agent_b_value: string,
    market_benchmark: string,     // "17–22%"
    verdict: "outlier" | "aligned" | "unverifiable",
    source_url: string,           // "https://gartner.com/..."
    source_name: string,          // "Gartner Enterprise SaaS Report 2026"
    note: string                  // "Agent A is 1.7x above market median"
  }>
}
```

**Stage 4 complete — `data` schema:**
```typescript
{
  path_a: {
    name: string,                 // "Hire 12 Engineers"
    description: string,
    success_condition: string,    // "IF pipeline closes above $2.8M by Q3"
    failure_condition: string,    // "IF close rate stays at 19%"
    recommended: boolean          // false
  },
  path_b: {
    name: string,                 // "Freeze Headcount"
    description: string,
    success_condition: string,
    failure_condition: string,
    recommended: boolean          // false
  },
  hybrid: {
    name: string,                 // "Hire 4 + Trigger"
    description: string,
    success_condition: string,
    failure_condition: string,
    recommended: boolean          // true
  }
}
```

**Stage 5 complete — `data` schema:**
```typescript
{
  context: string,
  divergence_finding: string,
  recommended_decision: string,
  rationale: string,
  dissenting_opinion: string,
  trigger_conditions: string[],    // exactly 3 items
  audit_log: Array<{
    claim: string,
    source_url: string,
    source_name: string
  }>
}
```

---

## Full SSE Stream Example

This is what the frontend receives when a run completes successfully:

```
data: {"stage": 1, "status": "loading", "message": "Loading Veris transcripts..."}\n\n

data: {"stage": 1, "status": "complete", "data": {"agent_a": {"recommendation": "Hire 12 engineers now", "assumptions": [{"variable": "close_rate", "value": "34%", "source": "internal_crm_q2"}], "source": "transcript_a.json"}, "agent_b": {"recommendation": "Freeze all headcount", "assumptions": [{"variable": "close_rate", "value": "19%", "source": "macro_benchmark"}], "source": "transcript_b.json"}}}\n\n

data: {"stage": 2, "status": "loading", "message": "Running forensics agent..."}\n\n

data: {"stage": 2, "status": "complete", "data": {"assumption_table": [{"variable": "close_rate", "agent_a_value": "34%", "agent_a_source": "internal_crm_q2", "agent_b_value": "19%", "agent_b_source": "macro_benchmark", "divergence_type": "data_conflict", "is_crux": true}], "divergence_type": "data_conflict", "finding": "Agents split at close rate: Agent A used 34% (internal CRM Q2) vs Agent B 19% (macro benchmark). Agent A's case collapses if close rate drops below 26%.", "crux_variable": "close_rate"}}\n\n

data: {"stage": 3, "status": "loading", "message": "Querying You.com for market benchmarks..."}\n\n

data: {"stage": 3, "status": "complete", "data": {"grounded_assumptions": [{"variable": "close_rate", "agent_a_value": "34%", "agent_b_value": "19%", "market_benchmark": "17–22%", "verdict": "outlier", "source_url": "https://gartner.com/en/sales/benchmarks", "source_name": "Gartner Sales Benchmarks 2026", "note": "Agent A is 1.7x above market median"}]}}\n\n

data: {"stage": 4, "status": "loading", "message": "Simulating outcome paths..."}\n\n

data: {"stage": 4, "status": "complete", "data": {"path_a": {"name": "Hire 12", "description": "Full hiring at optimistic close rate", "success_condition": "Pipeline closes above $2.8M by Q3", "failure_condition": "Close rate stays at 19% — runway drops to 6 months", "recommended": false}, "path_b": {"name": "Freeze", "description": "Preserve runway at all costs", "success_condition": "Macro recovers, conservative positioning becomes advantage", "failure_condition": "APAC window missed, pipeline velocity drops 30%", "recommended": false}, "hybrid": {"name": "Hire 4 + Trigger", "description": "Hedge on the close rate uncertainty", "success_condition": "Preserves 8mo runway, maintains 70% pipeline capacity", "failure_condition": "APAC window closes faster than modeled", "recommended": true}}}\n\n

data: {"stage": 5, "status": "loading", "message": "Generating decision brief..."}\n\n

data: {"stage": 5, "status": "complete", "data": {"context": "Two agents conflict on TechFlow headcount decision.", "divergence_finding": "The disagreement reduces to one number: close rate. Agent A used 34% (internal CRM Q2) — 1.7x above the Gartner market median of 17–22%.", "recommended_decision": "Hire 4 engineers now. Trigger: expand to 12 if Q3 pipeline closes above $3M.", "rationale": "Agent A's case depends on a 34% close rate — verified as an outlier by Gartner benchmarks. Until Q3 data confirms this assumption, full-scale hiring is a $216K/month bet on an outlier. The hybrid path preserves optionality.", "dissenting_opinion": "Agent B position: Even 4 hires reduces runway to 7.8 months. If macro conditions worsen beyond current benchmarks, the trigger clause may arrive too late to course-correct. Recommended action: full freeze until Q3 pipeline data is available.", "trigger_conditions": ["Expand to 12 if Q3 pipeline closes above $3M", "Reduce to 0 new hires if burn exceeds $900K/month", "Freeze expansion if enterprise SaaS macro index drops below Q1 baseline"], "audit_log": [{"claim": "Close rate market benchmark 17–22%", "source_url": "https://gartner.com/en/sales/benchmarks", "source_name": "Gartner Sales Benchmarks 2026"}, {"claim": "APAC enterprise SaaS market growing 18% YoY", "source_url": "https://idc.com/apac-saas-2026", "source_name": "IDC APAC SaaS Market Report"}]}}\n\n

data: {"stage": "done", "status": "complete"}\n\n
```

---

## Frontend SSE Parsing

```typescript
// frontend/app/page.tsx

const runArbitration = () => {
  const eventSource = new EventSource('/api/run')

  eventSource.onmessage = (event) => {
    const parsed = JSON.parse(event.data)

    if (parsed.status === 'loading') {
      setLoadingStage(parsed.stage)
      setLoadingMessage(parsed.message)
    }

    if (parsed.status === 'complete' && parsed.stage !== 'done') {
      setStageData(prev => ({ ...prev, [parsed.stage]: parsed.data }))
      setCompletedStages(prev => [...prev, parsed.stage])
    }

    if (parsed.stage === 'done') {
      eventSource.close()
      setRunComplete(true)
    }

    if (parsed.status === 'error') {
      setError({ stage: parsed.stage, message: parsed.message })
      eventSource.close()
    }
  }

  eventSource.onerror = () => {
    setError({ stage: 'connection', message: 'Lost connection to backend' })
    eventSource.close()
  }
}
```

---

## FastAPI SSE Implementation

```python
# backend/main.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pipeline import run_pipeline

app = FastAPI()

@app.get("/api/run")
async def run():
    return StreamingResponse(
        run_pipeline(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering if applicable
        }
    )
```

```python
# backend/pipeline.py

import json
import asyncio
from typing import AsyncGenerator

async def run_pipeline() -> AsyncGenerator[str, None]:

    def event(stage, status, data=None, message=None) -> str:
        payload = {"stage": stage, "status": status}
        if data: payload["data"] = data
        if message: payload["message"] = message
        return f"data: {json.dumps(payload)}\n\n"

    # Stage 1
    yield event(1, "loading", message="Loading Veris transcripts...")
    transcripts = load_transcripts()
    stage1_data = parse_agent_outputs(transcripts)
    yield event(1, "complete", data=stage1_data)

    # Stage 2
    yield event(2, "loading", message="Running forensics agent...")
    forensics = await run_forensics(transcripts)
    yield event(2, "complete", data=forensics.dict())

    # Stage 3
    yield event(3, "loading", message="Querying You.com for market benchmarks...")
    grounding = await run_grounding(forensics)
    yield event(3, "complete", data=grounding.dict())

    # Stage 4
    yield event(4, "loading", message="Simulating outcome paths...")
    simulation = await run_simulation(forensics, grounding)
    yield event(4, "complete", data=simulation.dict())

    # Stage 5
    yield event(5, "loading", message="Generating decision brief...")
    brief = await run_brief(forensics, grounding, simulation)
    yield event(5, "complete", data=brief.dict())

    yield event("done", "complete")
```
