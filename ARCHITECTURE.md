# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER (Next.js)                        │
│                                                             │
│  [Run Arbitration] ──SSE──► PipelineBar                    │
│                             AgentCards                      │
│                             DivergenceTable                 │
│                             GroundingBadges                 │
│                             PathCards                       │
│                             BriefCard                       │
└─────────────────────┬───────────────────────────────────────┘
                      │  GET /api/run  (SSE stream)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  FASTAPI BACKEND (Python)                    │
│                                                             │
│  pipeline.py  ──► Stage 1: Load transcripts (disk)         │
│                   Stage 2: forensics.py ──► Baseten/Claude  │
│                   Stage 3: grounding.py ──► You.com API     │
│                   Stage 4: simulation.py ──► Baseten/Claude │
│                   Stage 5: brief.py ──► Baseten/Claude      │
│                                                             │
│  data/transcript_a.json  (pre-saved Veris output)          │
│  data/transcript_b.json  (pre-saved Veris output)          │
│  data/seed.json          (TechFlow hardcoded scenario)     │
└─────────────────────────────────────────────────────────────┘

PRE-RUN (before demo, not during):
┌─────────────────────────────────────────────────────────────┐
│                      VERIS AI (CLI)                          │
│                                                             │
│  veris env push (agent_a) ──► Veris Cloud                  │
│  veris env push (agent_b) ──► Veris Cloud                  │
│  veris run ──► simulations execute ──► transcripts saved   │
│                                                             │
│  Agent A: revenue_agent.py  (Baseten-powered)              │
│  Agent B: risk_agent.py     (Baseten-powered)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### Frontend (Next.js)

**Single responsibility:** Render the pipeline state. The frontend has no business logic. It only:
- Opens an SSE connection when the button is pressed
- Parses incoming stage events
- Renders the appropriate component for each completed stage

State management is simple — a `stageData` object keyed by stage number.

### Backend (FastAPI)

**Single responsibility:** Run the pipeline and stream events. The backend:
- Reads the pre-saved Veris transcripts from disk
- Runs each pipeline stage in sequence
- Yields SSE events as each stage completes
- Has no database, no auth, no session state

### Forensics Agent

**Single responsibility:** Find the divergence point.

Takes two transcripts. Extracts every named number each agent used. Classifies each into: agreed, data_conflict, missing_var, or horizon_mismatch. Identifies the single most critical divergence (the crux).

This is the product's moat. If this stage produces garbage output, everything downstream is wrong.

### Grounding Agent

**Single responsibility:** Verify disputed assumptions against live data.

Takes the divergence table. For each row with `divergence_type != "agreed"`, fires a You.com search. Returns a verdict (outlier / aligned / unverifiable) + a real source URL.

### Simulation Agent

**Single responsibility:** Produce conditional futures.

Takes the grounded divergence data. Produces three paths: Path A (follow Agent A), Path B (follow Agent B), Hybrid. Each path has named trigger conditions — not probability scores.

### Brief Agent

**Single responsibility:** Write the decision document.

Takes all upstream outputs. Produces a structured brief with 6 sections. The brief must read like a CFO wrote it — specific numbers, named conditions, no hedging language.

---

## Sequence Diagram

```
Browser          FastAPI          Baseten         You.com         Disk
   │                │                │               │              │
   │  GET /api/run  │                │               │              │
   │───────────────►│                │               │              │
   │                │  read files    │               │              │
   │                │───────────────────────────────────────────────►
   │                │◄───────────────────────────────────────────────
   │  stage:1 done  │                │               │              │
   │◄───────────────│                │               │              │
   │                │  forensics     │               │              │
   │                │  prompt        │               │              │
   │                │───────────────►│               │              │
   │                │◄───────────────│               │              │
   │  stage:2 done  │                │               │              │
   │◄───────────────│                │               │              │
   │                │  search(q1)    │               │              │
   │                │  search(q2)    │               │              │
   │                │  search(q3) ───────────────────►              │
   │                │◄───────────────────────────────│              │
   │  stage:3 done  │                │               │              │
   │◄───────────────│                │               │              │
   │                │  simulation    │               │              │
   │                │  prompt        │               │              │
   │                │───────────────►│               │              │
   │                │◄───────────────│               │              │
   │  stage:4 done  │                │               │              │
   │◄───────────────│                │               │              │
   │                │  brief         │               │              │
   │                │  prompt        │               │              │
   │                │───────────────►│               │              │
   │                │◄───────────────│               │              │
   │  stage:5 done  │                │               │              │
   │◄───────────────│                │               │              │
   │  stage:done    │                │               │              │
   │◄───────────────│                │               │              │
```

---

## Veris Integration Architecture

Veris is **not** part of the live runtime. It is a pre-run step that produces the input data for the live demo.

```
MORNING OF DEMO:
─────────────────────────────────────────────────────────────

Developer machine
    │
    ├── veris env push (agent_a/)  ──► Veris Cloud
    │       Builds Docker image
    │       Uploads to Veris
    │
    ├── veris env push (agent_b/)  ──► Veris Cloud
    │
    └── veris run \
            --scenario-set-id <id> \
            --env-id agent_a        ──► Simulation runs (~5 min)
                                         Agent A talks to mock Salesforce
                                         Agent A calls mock forecast API
                                         All tool calls logged
                                         Transcript saved to Veris console

    └── veris run \
            --scenario-set-id <id> \
            --env-id agent_b        ──► Simulation runs (~5 min)
                                         Agent B talks to mock finance model
                                         Agent B calls mock burn calculator
                                         All tool calls logged

    └── Download transcripts from Veris console
            → Save as backend/data/transcript_a.json
            → Save as backend/data/transcript_b.json

DEMO TIME:
─────────────────────────────────────────────────────────────

Button clicked → backend reads transcript_a.json and transcript_b.json from disk
               → pipeline runs on those saved transcripts
               → Veris is never called again
```

---

## Data Schemas

### Veris Transcript Schema (saved JSON)

```json
{
  "agent": "revenue_agent",
  "scenario": "techflow_hire_decision",
  "tool_calls": [
    {
      "tool": "salesforce.getOpportunities",
      "input": { "stage": "qualified" },
      "output": { "pipeline_value": 4200000, "deals": 23 },
      "timestamp": "2026-04-18T09:00:01Z"
    },
    {
      "tool": "forecast.getCloseRate",
      "input": { "source": "internal_crm", "period": "Q2" },
      "output": { "close_rate": 0.34, "confidence": "high" },
      "timestamp": "2026-04-18T09:00:02Z"
    }
  ],
  "reasoning_steps": [
    "Pipeline is $4.2M. Close rate at 34% yields $1.43M new ARR.",
    "At current velocity, 12 engineers needed to deliver by Q3.",
    "Recommendation: Hire 12 engineers immediately."
  ],
  "final_recommendation": "Hire 12 engineers now",
  "confidence": "high"
}
```

### Seed Data Schema

```json
{
  "company": "TechFlow Inc.",
  "stage": "Series A",
  "runway_dollars": 6000000,
  "burn_rate_monthly": 680000,
  "runway_months": 8.8,
  "engineers_current": 42,
  "pipeline_value": 4200000,
  "pipeline_region": "APAC",
  "decision_question": "Should we hire 12 engineers now or freeze headcount?",
  "agent_a_role": "Revenue optimization",
  "agent_b_role": "Risk management"
}
```

---

## Port Map

| Service | Port |
|---|---|
| Next.js frontend | 3000 |
| FastAPI backend | 8000 |

The frontend proxies `/api/run` to `http://localhost:8000/api/run`.
