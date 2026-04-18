# CLAUDE.md — Instructions for Claude Code

This file tells Claude Code everything it needs to know to work on this codebase effectively. Read this before touching any file.

---

## What This Project Is

A multi-agent conflict arbitration system called **Resolvr**. Two AI agents (Revenue and Risk) analyze the same company scenario and reach conflicting recommendations. This system finds where they diverged, verifies the disputed claims against live market data, simulates outcomes, and produces a structured decision brief.

**The core pipeline has 5 stages:**
1. Load Veris transcripts (pre-saved JSON, instant)
2. Forensics Agent — Claude call extracts assumption divergence
3. You.com grounding — live market verification per assumption
4. Simulation Agent — Claude call generates conditional outcome trees
5. Brief Agent — Claude call writes the final decision brief

---

## Critical Constraints — Read Before Writing Code

### Veris is CLI-only
Veris has no REST API. **Never** write code that tries to call Veris via HTTP at runtime. The Veris transcripts are pre-saved to `backend/data/transcript_a.json` and `backend/data/transcript_b.json`. Stage 1 just reads these files from disk. That is intentional.

### All LLM calls go through Baseten
Never call Anthropic API directly. Always use the Baseten client (`backend/utils/baseten_client.py`). The model ID is in the env var `BASETEN_MODEL_ID`.

### Output schemas are strict
Every pipeline stage returns a typed Pydantic model. **Never** return raw strings from pipeline stages. If a Claude call returns malformed JSON, retry once, then raise a PipelineError with stage context.

### The UI streams via SSE
The frontend does not poll. It opens a single SSE connection to `GET /api/run`. The backend sends stage update events as each stage completes. Do not break the SSE event format (see `API.md`).

### Seed data is hardcoded
The demo company TechFlow Inc. data lives in `backend/data/seed.json`. Never make the user enter a company name or any inputs. The demo runs on this fixed dataset.

---

## Codebase Map — Key Files

### Backend

| File | What it does |
|---|---|
| `backend/main.py` | FastAPI app. Two endpoints: `GET /health` and `GET /api/run` (SSE) |
| `backend/pipeline.py` | Orchestrates all 5 stages. Yields SSE events as each completes. This is the main file to understand. |
| `backend/pipeline_stages/forensics.py` | Stage 2. Reads both transcripts, calls Claude, returns `ForensicsOutput` |
| `backend/pipeline_stages/grounding.py` | Stage 3. Takes assumption list, fires You.com searches, returns `GroundingOutput` |
| `backend/pipeline_stages/simulation.py` | Stage 4. Takes grounded divergence, calls Claude, returns `SimulationOutput` |
| `backend/pipeline_stages/brief.py` | Stage 5. Takes all upstream outputs, calls Claude, returns `BriefOutput` |
| `backend/models.py` | All Pydantic models for stage inputs/outputs |
| `backend/prompts.py` | All Claude prompt templates. **Do not inline prompts in stage files.** |
| `backend/utils/baseten_client.py` | Baseten LLM client wrapper |
| `backend/utils/youcom_client.py` | You.com search client wrapper |
| `backend/data/seed.json` | TechFlow Inc. seed data |
| `backend/data/transcript_a.json` | Pre-saved Veris transcript for Agent A (Revenue) |
| `backend/data/transcript_b.json` | Pre-saved Veris transcript for Agent B (Risk) |

### Frontend

| File | What it does |
|---|---|
| `frontend/app/page.tsx` | Main page. Has the "Run Arbitration" button. Manages SSE connection and renders sections. |
| `frontend/components/PipelineBar.tsx` | 5-stage progress indicator. Accepts `activeStage` and `completedStages` props. |
| `frontend/components/AgentCards.tsx` | Side-by-side Agent A / Agent B recommendation cards |
| `frontend/components/DivergenceTable.tsx` | Assumption table. Highlights diverging rows red. |
| `frontend/components/GroundingBadges.tsx` | Renders verdict badges (OUTLIER / ALIGNED / UNVERIFIABLE) per assumption |
| `frontend/components/PathCards.tsx` | 3 outcome path cards. Hybrid card has green border. |
| `frontend/components/BriefCard.tsx` | Final brief. Left: recommendation + dissent. Right: triggers + audit log. |

---

## Data Flow — Step by Step

```
1. Button click
   → frontend sends GET /api/run
   → SSE connection opens

2. Backend loads seed.json + transcript_a.json + transcript_b.json
   → emits event: { stage: 1, status: "complete", data: { agentA, agentB } }

3. Forensics stage runs (Claude call ~3s)
   → emits event: { stage: 2, status: "complete", data: ForensicsOutput }

4. Grounding stage runs (You.com calls ~4s, parallel)
   → emits event: { stage: 3, status: "complete", data: GroundingOutput }

5. Simulation stage runs (Claude call ~4s)
   → emits event: { stage: 4, status: "complete", data: SimulationOutput }

6. Brief stage runs (Claude call ~5s)
   → emits event: { stage: 5, status: "complete", data: BriefOutput }

7. Backend emits: { stage: "done", status: "complete" }
   → SSE connection closes
```

Each `data` field in the SSE event is a JSON-stringified version of the corresponding Pydantic model.

---

## Pydantic Models Reference

These are the key types. Full definitions in `backend/models.py`.

```python
# Stage 1 output
class AgentOutput(BaseModel):
    recommendation: str          # "Hire 12 engineers now"
    assumptions: list[Assumption] # list of named numbers used
    source: str                  # "transcript_a.json"

class Assumption(BaseModel):
    variable: str    # "close_rate"
    value: str       # "34%"
    source: str      # "internal_crm_q2"
    raw_tool_call: str  # exact tool call from transcript

# Stage 2 output
class ForensicsOutput(BaseModel):
    assumption_table: list[AssumptionRow]
    divergence_type: str   # "data_conflict" | "missing_var" | "horizon_mismatch"
    finding: str           # one-sentence divergence statement
    crux_variable: str     # "close_rate" — the single most critical divergence

class AssumptionRow(BaseModel):
    variable: str
    agent_a_value: str
    agent_a_source: str
    agent_b_value: str
    agent_b_source: str
    divergence_type: str   # "data_conflict" | "missing_var" | "agreed"
    is_crux: bool          # True for the most critical divergence

# Stage 3 output
class GroundingOutput(BaseModel):
    grounded_assumptions: list[GroundedAssumption]

class GroundedAssumption(BaseModel):
    variable: str
    agent_a_value: str
    agent_b_value: str
    market_benchmark: str
    verdict: str        # "outlier" | "aligned" | "unverifiable"
    source_url: str
    source_name: str
    note: str

# Stage 4 output
class SimulationOutput(BaseModel):
    path_a: OutcomePath
    path_b: OutcomePath
    hybrid: OutcomePath

class OutcomePath(BaseModel):
    name: str
    description: str
    success_condition: str   # "IF pipeline closes above $2.8M by Q3"
    failure_condition: str
    recommended: bool

# Stage 5 output
class BriefOutput(BaseModel):
    context: str
    divergence_finding: str
    recommended_decision: str
    rationale: str
    dissenting_opinion: str
    trigger_conditions: list[str]   # 3 named conditions
    audit_log: list[AuditEntry]

class AuditEntry(BaseModel):
    claim: str
    source_url: str
    source_name: str
```

---

## Claude Prompt Engineering Rules

All prompts live in `backend/prompts.py`. Follow these rules strictly:

### Always request JSON output
Every Claude call must end with: `Respond ONLY with valid JSON. No preamble, no markdown, no explanation.`

### Always specify the exact output schema in the prompt
Include the Pydantic model fields in the prompt so Claude knows exactly what structure to return.

### The forensics prompt is the most critical
It must explicitly ask for:
- `variable` name (not a description — a machine-readable key like `close_rate`)
- `agent_a_value` and `agent_b_value` as strings with units
- `agent_a_source` and `agent_b_source`
- `divergence_type` from the allowed enum: `data_conflict`, `missing_var`, `horizon_mismatch`, `agreed`
- `is_crux: true` on the single most important divergence

If the forensics output is wrong, the entire pipeline produces garbage. Test this stage independently first.

### Parse defensively
```python
import json
import re

def parse_claude_json(raw: str) -> dict:
    # Strip markdown fences if present
    clean = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Retry once with a stricter prompt
        raise PipelineError(stage="forensics", message=f"Invalid JSON: {clean[:200]}")
```

---

## You.com Integration Rules

The You.com client lives in `backend/utils/youcom_client.py`.

### Fire searches in parallel
```python
import asyncio

queries = [
    "enterprise SaaS close rate benchmark 2026",
    "Series A SaaS burn multiple 2026",
    "APAC enterprise software market growth 2026"
]

results = await asyncio.gather(*[youcom_client.search(q) for q in queries])
```

### Filter for authoritative sources
After getting results, pass the source list to a quick Claude call to classify:
- `authoritative` — Gartner, IDC, Forrester, McKinsey, a16z, Bessemer, Saastr, major financial press
- `acceptable` — reputable tech blogs, industry reports
- `low_quality` — forums, personal blogs, low-DA sites

Only include `authoritative` sources in the brief audit log.

---

## SSE Event Format

The backend pipeline sends events in this exact format. Do not change it without updating the frontend SSE parser.

```
data: {"stage": 1, "status": "loading", "message": "Loading Veris transcripts..."}\n\n
data: {"stage": 1, "status": "complete", "data": {...}}\n\n
data: {"stage": 2, "status": "loading", "message": "Running forensics agent..."}\n\n
data: {"stage": 2, "status": "complete", "data": {...}}\n\n
...
data: {"stage": "done", "status": "complete"}\n\n
```

`status` is always either `"loading"` or `"complete"`.
`data` is only present on `"complete"` events.
`message` is only present on `"loading"` events.

---

## Error Handling

```python
class PipelineError(Exception):
    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message

# In pipeline.py — catch and emit as SSE error event
try:
    result = await run_forensics(transcripts)
except PipelineError as e:
    yield f"data: {json.dumps({'stage': e.stage, 'status': 'error', 'message': e.message})}\n\n"
    return
```

The frontend shows the error inline in the relevant stage section. The pipeline stops at the failed stage.

---

## Running Tests

```bash
# Test just the forensics stage with saved transcripts
cd backend
python -m pytest tests/test_forensics.py -v

# Test the full pipeline end to end (requires all API keys)
python -m pytest tests/test_pipeline.py -v

# Test without API calls (uses fixtures)
python -m pytest tests/ -v --mock-apis
```

---

## Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| `transcript_a.json not found` | Veris pre-run not done | Run `python backend/scripts/generate_mock_transcripts.py` for development |
| `BASETEN_API_KEY not set` | Missing env var | Copy `.env.example` to `.env` and fill in |
| `JSONDecodeError in forensics` | Claude returned markdown | The prompt must end with the JSON-only instruction |
| `SSE connection closes immediately` | FastAPI streaming not configured | Ensure `StreamingResponse` with `media_type="text/event-stream"` |
| `You.com returns no results` | Bad query or rate limit | Check `YOUCOM_API_KEY` is valid; add retry with backoff |

---

## Working Rules

### The 95% confidence rule
When you've reached ~95% certainty that a given approach or direction is correct, commit to it and move forward. Don't stall chasing the last 5% — ship the work and course-correct if something proves wrong.

### Test before declaring done
After writing code, exercise it yourself before saying it's finished. Run the relevant tests, hit the endpoint, or trigger the flow, and only then confirm whether the result is correct. "It compiles" is not a test.

---

## What NOT to Do

- **Do not** call Veris at runtime from any endpoint
- **Do not** let any Claude prompt return free text — always JSON
- **Do not** hardcode API keys anywhere — always use `os.getenv()`
- **Do not** make the user enter data — the seed is fixed
- **Do not** add a database — local JSON files only for the hackathon
- **Do not** use `time.sleep()` for fake loading delays — all delays are real API calls
