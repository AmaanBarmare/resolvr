# PIPELINE.md — Pipeline Stages & Prompts

All Claude prompts live in `backend/prompts.py`. All stages are in `backend/pipeline_stages/`. This document describes what each stage does, what prompt it uses, and what it must return.

---

## Stage 1 — Load Transcripts

**File:** `backend/pipeline.py` (not a separate stage file — just file I/O)

**What it does:**
1. Reads `backend/data/transcript_a.json`
2. Reads `backend/data/transcript_b.json`
3. Reads `backend/data/seed.json`
4. Extracts the top-level recommendation and assumptions from each transcript
5. Returns `Stage1Output`

**No Claude call.** This is pure JSON parsing.

```python
def load_transcripts() -> dict:
    with open("data/transcript_a.json") as f:
        transcript_a = json.load(f)
    with open("data/transcript_b.json") as f:
        transcript_b = json.load(f)
    return {"agent_a": transcript_a, "agent_b": transcript_b}

def parse_agent_outputs(transcripts: dict) -> dict:
    a = transcripts["agent_a"]
    b = transcripts["agent_b"]
    return {
        "agent_a": {
            "recommendation": a["final_recommendation"],
            "assumptions": a["key_assumptions"],
            "source": "transcript_a.json"
        },
        "agent_b": {
            "recommendation": b["final_recommendation"],
            "assumptions": b["key_assumptions"],
            "source": "transcript_b.json"
        }
    }
```

---

## Stage 2 — Forensics Agent

**File:** `backend/pipeline_stages/forensics.py`

**What it does:**
Reads both full transcripts. Extracts every named number. Compares them. Classifies each divergence. Identifies the crux (single most important point of disagreement).

**Input:** Both transcript JSON objects

**Output:** `ForensicsOutput` Pydantic model

**Prompt:**

```python
FORENSICS_PROMPT = """
You are a forensic analyst examining two AI agent outputs to find where their reasoning diverged.

AGENT A TRANSCRIPT:
{transcript_a}

AGENT B TRANSCRIPT:
{transcript_b}

Your task:
1. Extract every named number, assumption, or data point each agent used
2. Compare them side by side
3. Classify each comparison

Divergence types:
- "data_conflict": Both agents modeled the same variable but used different values
- "missing_var": One agent modeled a variable the other ignored entirely
- "horizon_mismatch": Both agents used the same data but over different time periods
- "agreed": Both agents used the same value

4. Identify the single most critical divergence — the one that, if resolved, would most change the outcome. Set is_crux: true on that row.

5. Write a one-sentence finding that names the exact variable and values.

Respond ONLY with valid JSON matching this exact structure. No preamble, no markdown, no explanation:

{
  "assumption_table": [
    {
      "variable": "snake_case_key",
      "agent_a_value": "value with units",
      "agent_a_source": "where agent A got this",
      "agent_b_value": "value with units or 'not modeled'",
      "agent_b_source": "where agent B got this or 'n/a'",
      "divergence_type": "data_conflict | missing_var | horizon_mismatch | agreed",
      "is_crux": true | false
    }
  ],
  "divergence_type": "primary divergence type for the overall conflict",
  "finding": "one sentence: agents split at [variable]: Agent A used [value] ([source]) vs Agent B [value] ([source]). Agent A's case collapses if [variable] drops below [threshold].",
  "crux_variable": "snake_case_key of the crux row"
}
"""
```

**Implementation:**

```python
async def run_forensics(transcripts: dict) -> ForensicsOutput:
    prompt = FORENSICS_PROMPT.format(
        transcript_a=json.dumps(transcripts["agent_a"], indent=2),
        transcript_b=json.dumps(transcripts["agent_b"], indent=2)
    )

    raw = await baseten_client.complete(prompt)
    parsed = parse_claude_json(raw)  # strips markdown, parses JSON

    # Validate required fields
    assert "assumption_table" in parsed
    assert "finding" in parsed
    assert any(row["is_crux"] for row in parsed["assumption_table"])

    return ForensicsOutput(**parsed)
```

**What good output looks like:**

```json
{
  "assumption_table": [
    {
      "variable": "close_rate",
      "agent_a_value": "34%",
      "agent_a_source": "internal_salesforce_crm_q2",
      "agent_b_value": "19%",
      "agent_b_source": "macro_enterprise_saas_benchmark",
      "divergence_type": "data_conflict",
      "is_crux": true
    },
    {
      "variable": "pipeline_value",
      "agent_a_value": "$4.2M",
      "agent_a_source": "salesforce",
      "agent_b_value": "$4.2M",
      "agent_b_source": "salesforce",
      "divergence_type": "agreed",
      "is_crux": false
    },
    {
      "variable": "macro_outlook",
      "agent_a_value": "not modeled",
      "agent_a_source": "n/a",
      "agent_b_value": "contracting",
      "agent_b_source": "cb_insights_q1_2026",
      "divergence_type": "missing_var",
      "is_crux": false
    }
  ],
  "divergence_type": "data_conflict",
  "finding": "Agents split at close_rate: Agent A used 34% (internal CRM Q2) vs Agent B 19% (macro benchmark). Agent A's entire case collapses if close rate drops below 26%.",
  "crux_variable": "close_rate"
}
```

---

## Stage 3 — You.com Grounding

**File:** `backend/pipeline_stages/grounding.py`

**What it does:**
Takes the divergent assumptions from Stage 2. For each `data_conflict` or `missing_var` row, fires a You.com search. Verifies each claim against live market data. Returns a verdict + source URL per assumption.

**Input:** `ForensicsOutput` from Stage 2

**Output:** `GroundingOutput` Pydantic model

**Implementation:**

```python
async def run_grounding(forensics: ForensicsOutput) -> GroundingOutput:
    # Only ground assumptions that diverge
    to_ground = [
        row for row in forensics.assumption_table
        if row.divergence_type in ("data_conflict", "missing_var")
    ]

    # Build search queries
    queries = [build_search_query(row, seed_data) for row in to_ground]

    # Fire in parallel
    results = await asyncio.gather(*[youcom_client.search(q) for q in queries])

    # Score source quality, extract benchmark, assign verdict
    grounded = [
        process_grounding_result(row, result)
        for row, result in zip(to_ground, results)
    ]

    return GroundingOutput(grounded_assumptions=grounded)


def build_search_query(row: AssumptionRow, seed: dict) -> str:
    queries = {
        "close_rate": "enterprise B2B SaaS close rate benchmark 2026",
        "burn_rate": "Series A SaaS burn rate benchmark 2026",
        "runway_months": "Series A startup runway months 2026",
        "macro_outlook": "enterprise SaaS market growth outlook 2026",
        "arr_growth": "Series A SaaS ARR growth benchmark 2026",
    }
    return queries.get(row.variable, f"{row.variable} benchmark enterprise SaaS 2026")
```

**Source quality filter:**

```python
AUTHORITATIVE_DOMAINS = [
    "gartner.com", "idc.com", "forrester.com", "mckinsey.com",
    "a16z.com", "bvp.com", "saastr.com", "openviewpartners.com",
    "tomtunguz.com", "nytimes.com", "wsj.com", "techcrunch.com",
    "reuters.com", "bloomberg.com"
]

def is_authoritative(url: str) -> bool:
    return any(domain in url for domain in AUTHORITATIVE_DOMAINS)
```

**Verdict logic:**

```python
def assign_verdict(row: AssumptionRow, benchmark: str) -> str:
    # If agent A's value is more than 50% above the benchmark median → outlier
    # If within 20% of benchmark → aligned
    # If no reliable benchmark found → unverifiable
    ...
```

---

## Stage 4 — Simulation Agent

**File:** `backend/pipeline_stages/simulation.py`

**What it does:**
Takes the grounded divergence data. Generates three conditional outcome paths: Path A (follow Agent A), Path B (follow Agent B), and Hybrid. Each path has named trigger conditions — not probability scores.

**Input:** `ForensicsOutput` + `GroundingOutput`

**Output:** `SimulationOutput` Pydantic model

**Prompt:**

```python
SIMULATION_PROMPT = """
You are simulating the downstream outcomes of two conflicting business decisions.

COMPANY CONTEXT:
{seed_data}

DIVERGENCE MAP:
{forensics_summary}

GROUNDED MARKET DATA:
{grounding_summary}

Generate three outcome paths. For each path, state NAMED TRIGGER CONDITIONS — not probability scores.
A trigger condition is a specific, measurable event (e.g. "IF Q3 pipeline closes above $3M").

Path A: Follow Agent A's recommendation exactly.
Path B: Follow Agent B's recommendation exactly.
Hybrid: A middle path that hedges the key uncertainty.

For Hybrid, the key uncertainty is always the crux variable: {crux_variable}.

Respond ONLY with valid JSON. No preamble, no markdown:

{
  "path_a": {
    "name": "short name",
    "description": "2–3 sentence description",
    "success_condition": "IF [specific measurable condition]",
    "failure_condition": "IF [specific measurable condition]",
    "recommended": false
  },
  "path_b": {
    "name": "short name",
    "description": "2–3 sentence description",
    "success_condition": "IF [specific measurable condition]",
    "failure_condition": "IF [specific measurable condition]",
    "recommended": false
  },
  "hybrid": {
    "name": "short name",
    "description": "2–3 sentence description — include the specific hire count and trigger threshold",
    "success_condition": "IF [specific measurable condition]",
    "failure_condition": "IF [specific measurable condition]",
    "recommended": true
  }
}
"""
```

---

## Stage 5 — Brief Agent

**File:** `backend/pipeline_stages/brief.py`

**What it does:**
Takes all upstream outputs. Writes the final decision brief. The brief must read like a real CFO document — specific numbers, named conditions, no hedging language like "it depends" or "it's complicated."

**Input:** `ForensicsOutput` + `GroundingOutput` + `SimulationOutput`

**Output:** `BriefOutput` Pydantic model

**Prompt:**

```python
BRIEF_PROMPT = """
You are writing a 1-page executive decision brief for a board-level audience.

COMPANY: {company_name}
DECISION QUESTION: {decision_question}

FORENSICS FINDING:
{finding}

GROUNDED MARKET DATA:
{grounding_summary}

SIMULATION OUTCOMES:
Path A: {path_a_summary}
Path B: {path_b_summary}
Hybrid (recommended): {hybrid_summary}

Write a professional decision brief. Requirements:
- Recommended decision must be a single actionable sentence with a number and a condition
- Rationale must cite the specific market benchmark from the grounding data
- Dissenting opinion must represent Agent B's strongest case, not a strawman
- Exactly 3 trigger conditions — each must be specific and measurable
- Audit log must cite every factual claim made in the brief

Do NOT use phrases like "it depends", "various factors", or "it's complicated".
Every statement must be specific and measurable.

Respond ONLY with valid JSON. No preamble, no markdown:

{
  "context": "1–2 sentences describing the conflict",
  "divergence_finding": "1–2 sentences naming the exact crux variable and values",
  "recommended_decision": "single actionable sentence with specific number and trigger",
  "rationale": "2–3 sentences citing specific benchmarks and data points",
  "dissenting_opinion": "2–3 sentences representing Agent B's strongest case",
  "trigger_conditions": [
    "condition 1 — expand trigger",
    "condition 2 — pullback trigger",
    "condition 3 — abort trigger"
  ],
  "audit_log": [
    {
      "claim": "the factual claim made in the brief",
      "source_url": "https://...",
      "source_name": "Source name"
    }
  ]
}
"""
```

**What good brief output looks like:**

```json
{
  "context": "TechFlow's Revenue and Risk agents both analyzed the APAC hiring decision and reached opposite conclusions based on different close rate assumptions.",
  "divergence_finding": "The agents agree on pipeline value ($4.2M) but disagree on close rate: Agent A used 34% (internal CRM Q2) vs Agent B's 19% (macro benchmark). The Gartner 2026 benchmark confirms 17–22% as market median — Agent A is 1.7x above it.",
  "recommended_decision": "Hire 4 engineers now. Trigger to 12 if Q3 pipeline closes above $3M.",
  "rationale": "Agent A's hiring case depends on a 34% close rate, which Gartner benchmarks as an outlier at 1.7x the market median of 17–22%. Until Q3 data validates this assumption, full-scale hiring is a $216K/month bet on an unverified number. The hybrid path preserves 8 months of runway while maintaining 70% of pipeline execution capacity.",
  "dissenting_opinion": "Agent B's position: Even 4 hires reduces runway from 9 to 7.8 months. If the macro enterprise SaaS slowdown accelerates beyond current benchmarks, the Q3 trigger threshold may be unreachable, and the company will have burned $72K per hire with no expansion path. Recommended action: full headcount freeze until Q3 data confirms Agent A's close rate assumption.",
  "trigger_conditions": [
    "Expand to 12 engineers if Q3 pipeline closes above $3M ARR",
    "Freeze all expansion if monthly burn exceeds $900K for 2 consecutive months",
    "Cancel APAC initiative if enterprise SaaS macro index drops below Q1 2026 baseline by more than 15%"
  ],
  "audit_log": [
    {
      "claim": "Enterprise SaaS close rate market median 17–22%",
      "source_url": "https://gartner.com/en/sales/insights/saas-sales-benchmarks",
      "source_name": "Gartner Enterprise SaaS Sales Benchmarks 2026"
    },
    {
      "claim": "APAC enterprise software market growing 18% YoY",
      "source_url": "https://idc.com/getdoc.jsp?containerId=AP49823",
      "source_name": "IDC APAC Enterprise Software Market Forecast 2026"
    }
  ]
}
```

---

## Baseten Client

```python
# backend/utils/baseten_client.py

import os
import httpx

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_ID = os.getenv("BASETEN_MODEL_ID", "claude-sonnet-4-5")

async def complete(prompt: str, max_tokens: int = 2000) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://bridge.baseten.co/v1/direct",
            headers={
                "Authorization": f"Api-Key {BASETEN_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": BASETEN_MODEL_ID,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
```

---

## JSON Parse Helper

Used by every stage that calls Claude:

```python
# backend/utils/json_utils.py

import json
import re
from exceptions import PipelineError

def parse_claude_json(raw: str, stage: str) -> dict:
    """Strip markdown fences and parse JSON. Raises PipelineError on failure."""
    clean = re.sub(r"```json\s*|```\s*", "", raw).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise PipelineError(
            stage=stage,
            message=f"Claude returned invalid JSON: {str(e)}. Raw: {clean[:300]}"
        )
```

---

## Prompt Engineering Checklist

Before shipping any prompt, verify:

- [ ] Ends with: `Respond ONLY with valid JSON. No preamble, no markdown, no explanation:`
- [ ] Includes the exact JSON schema the stage expects
- [ ] Uses snake_case keys (not camelCase, not "Close Rate")
- [ ] All enum values are listed explicitly (`"data_conflict" | "missing_var" | ...`)
- [ ] Tested against at least 3 different input variations
- [ ] Handles the case where a field might be "not modeled" or "n/a"
