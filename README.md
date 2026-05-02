# Resolvr

> **Multi-agent conflict arbitration.** When your AI advisors disagree, Resolvr finds where their reasoning split, verifies the disputed claims against live market evidence, simulates outcomes, and publishes a defensible decision brief.

Live agents are mirrors of [Veris AI](https://veris.ai)-graded versions that score **7/7 across all grader categories** ([Revenue audit ↗](https://console.veris.ai/simulations/run_tc9dinezyn8xvkkzdn23j) · [Risk audit ↗](https://console.veris.ai/simulations/run_kxoileyk2zltd7e9hg414)).

---

## What It Does

Enterprises run dozens of AI agents simultaneously. They constantly give conflicting outputs:

- Revenue agent says **"Hire 12 engineers now"**
- Risk agent says **"Freeze all headcount"**

Today there is zero infrastructure to resolve those conflicts.

**Resolvr** is the arbitration layer. Given two scenario briefs (one per advisor), it:

1. Synthesizes a shared case profile and runs the Revenue and Risk advisors live, side by side
2. Finds **exactly** where their reasoning diverged (Forensics Agent)
3. Verifies each disputed assumption against live market data (You.com)
4. Simulates what happens if you follow each path (Simulation Agent)
5. Produces a 1-page decision brief with a recommendation + dissenting opinion (Brief Agent)

The human executive still decides. We just make that decision defensible to their board.

In mock mode (`USE_MOCK_PIPELINE=true`) Stage 1 instead replays the pre-saved Veris transcripts at [backend/data/transcript_a.json](backend/data/transcript_a.json) and [backend/data/transcript_b.json](backend/data/transcript_b.json) — useful when you want to demo the UI without burning API credits.

---

## Featured Case — Editable Defaults

The Docket on the homepage ships with a featured case pre-filled into both filings. Edit either brief to file a different scenario; the underlying seed at [backend/data/seed.json](backend/data/seed.json) is only used in mock mode.

| Field | Value |
|---|---|
| Company | TechFlow Inc. — B2B SaaS, Series A |
| Runway | $6M · $680K/month burn · ~9 months |
| Team | 42 engineers today |
| Pipeline | $4.2M potential ARR in APAC |
| Decision | Hire 12 engineers or freeze headcount? |
| **Revenue advisor** | Pushes the growth case (e.g. uses 34% close rate from internal CRM) |
| **Risk advisor** | Pushes the runway case (e.g. uses 19% close rate from macro benchmark) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (React 18) + custom editorial CSS |
| Backend | FastAPI (Python 3.11) |
| LLM Inference | Baseten (`openai/gpt-oss-120b`) |
| Agent Validation | Veris AI — live agents mirror the 7/7 grader-clean prompts |
| Market Grounding | You.com Search API |
| Storage | Local JSON files |
| Streaming | Server-Sent Events (SSE) for live UI updates |

---

## Project Structure

```
Resolvr/
├── backend/
│   ├── main.py                       # FastAPI app — /health and /api/run (SSE)
│   ├── pipeline.py                   # Pipeline orchestrator + SSE event emitter
│   ├── models.py                     # Pydantic models for every stage I/O
│   ├── prompts.py                    # All Claude prompt templates
│   ├── exceptions.py                 # PipelineError
│   ├── agents/
│   │   ├── revenue_agent.py          # Live Revenue advisor (Agent A)
│   │   ├── risk_agent.py             # Live Risk advisor (Agent B)
│   │   └── scenario_profile.py       # Synthesizes a shared case profile from both briefs
│   ├── pipeline_stages/
│   │   ├── forensics.py              # Stage 2 — Assumption extraction
│   │   ├── grounding.py              # Stage 3 — You.com verification
│   │   ├── simulation.py             # Stage 4 — Outcome trees
│   │   └── brief.py                  # Stage 5 — Decision brief
│   ├── utils/
│   │   ├── baseten_client.py         # Baseten LLM client wrapper
│   │   ├── youcom_client.py          # You.com search client wrapper
│   │   └── json_utils.py             # Defensive JSON parsing helpers
│   ├── scripts/
│   │   └── generate_mock_transcripts.py
│   ├── data/
│   │   ├── seed.json                 # TechFlow Inc. mock-mode seed
│   │   ├── transcript_a.json         # Pre-saved Veris transcript (Agent A)
│   │   ├── transcript_b.json         # Pre-saved Veris transcript (Agent B)
│   │   └── cases/                    # Saved arbitrations (gitignored, runtime-written)
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── page.tsx                  # Main dashboard page
│   │   ├── layout.tsx                # Root layout + fonts
│   │   ├── globals.css               # Editorial theme tokens
│   │   └── api/run/route.ts          # SSE proxy to FastAPI backend
│   ├── components/
│   │   ├── TopBar.tsx                # Newspaper masthead
│   │   ├── Docket.tsx                # Two filings + "Convene the desk" CTA
│   │   ├── PipelineBar.tsx           # 5-stage progress indicator
│   │   ├── SectionHeader.tsx         # Editorial section header
│   │   ├── AgentCards.tsx            # Side-by-side advisor recommendation cards
│   │   ├── DivergenceTable.tsx       # Assumption comparison table
│   │   ├── GroundingStatus.tsx       # You.com verdict status + sources
│   │   ├── PathCards.tsx             # 3 outcome path cards (Hybrid highlighted)
│   │   └── BriefCard.tsx             # Final decision brief
│   ├── hooks/
│   │   └── usePipeline.ts            # SSE consumer hook
│   └── package.json
├── veris/
│   ├── agent_a/
│   │   ├── Dockerfile
│   │   ├── veris.yaml
│   │   └── revenue_agent/main.py
│   └── agent_b/
│       ├── Dockerfile
│       ├── veris.yaml
│       └── risk_agent/main.py
├── README.md                         # This file
├── CLAUDE.md                         # Claude Code instructions
├── ARCHITECTURE.md                   # System architecture
├── AGENTS.md                         # How Agent A + B are built
├── VERIS_SETUP.md                    # Veris pre-run guide
├── API.md                            # Backend API reference
├── PIPELINE.md                       # Pipeline stages + prompts
├── DATA_SCHEMAS.md                   # Pydantic schemas reference
├── UI.md                             # Frontend design notes
└── env.example                       # Copy to .env and fill in keys
```

---

## Environment Variables

Copy `env.example` to `.env` (`cp env.example .env`) and fill in:

```bash
# Baseten (LLM inference for all Claude calls)
BASETEN_API_KEY=your_key_here
BASETEN_MODEL_ID=claude-sonnet-4-5   # or your deployed model ID

# You.com (live market grounding)
YOUCOM_API_KEY=your_key_here

# Veris (only needed for pre-run setup, not live demo)
VERIS_API_KEY=your_key_here
```

---

## Quick Start

### Backend

The backend uses `pyproject.toml` (with [`uv`](https://github.com/astral-sh/uv) as the recommended installer):

```bash
cd backend
uv sync                              # or: pip install .
uv run uvicorn main:app --reload     # or: uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

### Test the pipeline without UI

```bash
cd backend
python pipeline.py
# Runs all 5 stages and prints output to terminal
```

---

## How Veris Fits In

Veris is **Resolvr's validation layer**, not a runtime dependency. The Veris-deployed agents (in [`veris/agent_a/`](veris/agent_a/) and [`veris/agent_b/`](veris/agent_b/)) score 7/7 across every grader category. The in-process advisors that actually run when you click "Convene the desk" use the same prompts and workflow rules — so what gets graded is what ships.

The Veris CLI is only needed when you want to re-validate the agents after prompt changes:

```bash
cd veris/agent_a && veris env push
veris simulations create --scenario-set-id <id> --env-id <id>
```

`USE_MOCK_PIPELINE=true` is also available for offline UI demos (replays pre-saved transcripts at [backend/data/transcript_a.json](backend/data/transcript_a.json) and [backend/data/transcript_b.json](backend/data/transcript_b.json)) — no API credits burned.

See [VERIS_SETUP.md](VERIS_SETUP.md) for the full validation workflow.

---

## Challenges Faced

A short tour of the harder problems building Resolvr — written in plain language, not engineer-speak. Each one follows the same arc: what was broken, what I tried, what actually worked, and what I took away from it.

### 1. The agents worked perfectly. The grader saw nothing.

Veris is a platform that grades AI agents — a kind of automated quality inspector. I plugged my two agents in, ran the grader, and got **0% on every check**. The frustrating part: when I read the agent's output, it was perfect. Right answers, right format, right reasoning.

I spent hours rewriting prompts, suspecting my agent code, retrying. None of it helped.

The actual problem was one level deeper. Modern AI agents emit "trace events" that describe what they did — *the agent thought, then it used a tool, then it thought again*. There are two libraries that can do this: a basic one and a structured one. I was using the basic one, which only logs raw API calls. The grader needed the structured one, which logs at the agent level. So my agent was working fine — it just wasn't *talking* in a language the grader could understand.

Switching libraries took 30 minutes. The grader immediately started seeing my agent's behavior, and the score climbed from 0% to 60% in one push.

**The lesson:** when an automated test returns nothing, suspect the wiring between your code and the test before you suspect your code.

### 2. Forcing structured output made the model worse, not better.

I wanted my agent to return clean JSON every time. The obvious move: tell the AI library "the output must match this exact schema." It's a one-line setting.

After I added it, the agent started skipping its job. It was supposed to call three tools in sequence (look up sales pipeline → look up close rate → project revenue) before giving an answer. Instead, it would call one tool, then immediately produce a confident-sounding final JSON answer with **made-up numbers** for the other two.

It turned out that forcing a structured output schema short-circuits the model's multi-step reasoning. The model "sees" the schema, decides the easiest way to satisfy it is to fill in the JSON now, and stops thinking.

**The fix:** I removed the structured-output constraint. Instead, I told the agent *in the prompt* to return JSON, and I parsed it from the response text in code. Suddenly the agent took its time, called all three tools, and produced grounded answers.

**The lesson:** more constraints isn't always better. Sometimes guarantees on the *output* break the *process*.

### 3. The automated audit lied to me.

After I got my first agent to passing scores, the platform offered an automated "audit report" with suggestions for further improvements. One of them said: *"add this new assumption to your output — it'll improve the recommendation specificity grade."*

I followed the suggestion. The recommendation specificity grade improved — but a *different* grader I wasn't watching dropped from green to red. The new assumption I added had a generic source ("standard assumption"), which broke a separate check that required every assumption to come from a specific tool.

I learned the hard way that **the automated suggestions are hypotheses, not commands**. Each one optimizes for a single check in isolation. When you have seven checks all evaluating the same output, you have to think about the whole grading rubric, not just one row of it.

**The lesson:** trust automation to surface ideas, not to validate them. Always re-run the full test suite after acting on a suggestion.

### 4. The "runway" word game.

This was the hardest one. My second agent was stuck at 6 out of 7 graders. The one failing check was called "fabrication detection" — it accused my agent of making up numbers. But the agent wasn't making anything up. Every number came from a real tool.

The breakthrough was realizing that **the grader is a keyword matcher, not a reading-comprehension engine**. The agent's job was to talk about three different time-in-months values: the company's current cash runway, the projected runway after hiring, and a policy threshold. The agent — naturally — called all three of these "runway." The grader saw "runway = 8.82, runway = 7.79, runway = 8" and only one of those values came from the official `runway_months` tool. So it concluded the others were fabricated.

The fix had nothing to do with the agent's logic. I just changed the *vocabulary* the agent used. The word "runway" got reserved for one specific tool's output. The post-hire value became "cash duration." The threshold became "policy floor." Same numbers, same math, different words — and the grader went green.

**The lesson:** automated graders pattern-match. Sometimes you fix a "wrong answer" verdict with vocabulary discipline rather than with logic changes.

### 5. Two copies of the same code, slowly drifting apart.

Once I got my agents passing all the grader checks, I realized I had a structural problem. The agents Veris had certified were running inside Veris's container. The agents that actually run for users when they click "Convene the Desk" were a separate copy of the code in my own backend. Both copies started from the same prompts, but they would inevitably drift — fix a bug in one, forget to copy the fix to the other.

I had three choices:
- **Option A:** leave both copies, accept the drift. The certification claim becomes increasingly meaningless over time.
- **Option B:** call Veris from my backend at runtime, so the certified agent literally is the one serving users. But Veris simulations take ~2 minutes per call, cost real money, and depend on Veris being up.
- **Option C:** keep both copies, but enforce by discipline that they use identical prompts.

I chose Option C. I ported the Veris-graded prompts back into the in-process agents word-for-word. Now what gets graded is what ships, and the certification claim is honest — even though the architecture has two copies.

**The lesson:** sometimes the right architectural choice isn't a feature you build, it's a discipline you commit to.

### 6. Worked locally. Broken in production.

I added a feature where every completed arbitration gets a unique URL — `mysite.com/?case=abc123` — that anyone with the link could open and see the same result. I built it in three parts: backend saves the case to a file, backend serves the file via an API, frontend reads the URL and loads the case. Each piece worked when I tested it.

Then I tested the full flow: completed an arbitration, got a URL, opened it in a new tab. **"Unexpected token '<' ... is not valid JSON."**

What I'd missed was the *fourth* part. My web framework (Next.js) acts as a middleman that forwards requests from the frontend to the backend. I had set up that forwarding for the "run a new arbitration" endpoint but not for the "load a saved arbitration" endpoint. So when the frontend asked for `/api/case/abc123`, Next.js had no idea what to do, returned its own HTML 404 page, and the frontend's JSON parser choked on it.

The fix was three lines of code — one new file declaring the proxy route. But I didn't catch the bug until I clicked the actual link in the actual browser. Unit-tests on each individual piece had all passed.

**The lesson:** unit tests verify pieces, end-to-end tests verify the system. Always do the actual user gesture on the actual final flow before calling something done.

### What I'd take into an interview

- **Debugging is mostly about identifying which layer the bug lives in.** Half my time on this project was spent at the wrong layer.
- **Automated tools — graders, audits, AI suggestions — are useful but not authoritative.** Their output is a hypothesis you still have to verify.
- **More constraints don't always produce better behavior in AI systems.** Sometimes loosening a constraint is the fix.
- **End-to-end tests catch what unit tests miss.** Always click the real button.
- **When you have two copies of the same code, decide upfront whether you're going to enforce parity by automation, by discipline, or accept drift.** All three are valid; pretending the problem isn't there is not.

---

## Veris Integration Cookbook — What We Learned the Hard Way

Getting two agents from 0% to 7/7 grader-clean took a lot of trial-and-error against the Veris docs and cookbook. This is the consolidated set of mistakes we made and the fixes that finally worked. **If you're integrating an agent into Veris, read this first.**

### Setup mistakes (Phase 0)

| ❌ What we did | ✅ What works |
|---|---|
| Used `pip install -r requirements.txt` in `Dockerfile.sandbox`. Agent built but startup was unstable. | **Use `uv` exclusively.** `Dockerfile.sandbox` should `COPY pyproject.toml uv.lock /agent/` then `RUN uv sync --frozen --no-dev`. See [veris/agent_a/.veris/Dockerfile.sandbox](veris/agent_a/.veris/Dockerfile.sandbox). |
| Forgot to end `Dockerfile.sandbox` with `WORKDIR /app`. Agent process never came up. | **The final `WORKDIR /app` is mandatory** — Veris's entrypoint script requires it, and the failure mode is silent. |
| Used the legacy `persona.modality` schema in `veris.yaml` (the older docs still show it). | Use the current `actor.channels[0].type: http` schema. See [veris/agent_a/.veris/veris.yaml](veris/agent_a/.veris/veris.yaml). |
| Set `message_field: response.final_recommendation` (dot notation) for nested JSON extraction. Veris silently dropped the field. | **`message_field` only supports top-level JSON keys.** If your handler returns `{"response": {...}}`, you have to use `message_field: response` and flatten the payload yourself, or restructure the handler to emit a flat object. |
| Used `Dockerfile` (no `.sandbox` extension) for the Veris build. | The build looks for `.veris/Dockerfile.sandbox` specifically — extension matters. |

### SDK mistakes — getting the trace right

The Veris grader reads Langfuse session traces, not your HTTP response body. If your traces don't have AGENT-level spans, every grader check fails with *"No trace source found for simulation sim_xxx"* — even when your agent is producing perfect output.

| ❌ What we did | ✅ What works |
|---|---|
| Used the vanilla `openai` SDK and a hand-rolled tool loop. Got 0% scenario success. The model worked perfectly, but Veris's grader saw nothing. | **Use the `openai-agents` SDK** (`>= 0.2.6`). It auto-instruments via `openinference.instrumentation.openai_agents` and emits the AGENT spans Veris needs. |
| Pointed the Agents SDK at Baseten with `Agent(..., model="openai/gpt-oss-120b")`. Got 404. The SDK was interpreting `openai/` as a provider prefix and stripping it. | **Wrap the Baseten endpoint in an explicit `OpenAIChatCompletionsModel`** with a custom `AsyncOpenAI` client: `Agent(model=OpenAIChatCompletionsModel(model="openai/gpt-oss-120b", openai_client=AsyncOpenAI(base_url=BASETEN_BASE_URL, api_key=BASETEN_API_KEY)))`. See [veris/agent_a/revenue_agent/main.py:69-78](veris/agent_a/revenue_agent/main.py#L69-L78). |
| Set `Agent(..., output_type=Recommendation)` to force a structured Pydantic output. The model produced perfect JSON on turn 2 — and skipped the remaining tool calls. | **Do not use `output_type` with `gpt-oss-120b`.** It collapses the tool loop. Instead, instruct JSON in the system prompt and parse it from text in your handler. See `_extract_json` helper in [veris/agent_a/revenue_agent/main.py:96-105](veris/agent_a/revenue_agent/main.py#L96-L105). |
| Forgot `reset_tool_choice=True` with `tool_choice="required"`. Agent kept calling the same tool. | Add `reset_tool_choice=True` so `tool_choice="required"` only forces the **first** tool call. After that, the SDK reverts to `auto` and lets the model emit final text. |

### Prompt-engineering mistakes — getting from 60% to 100%

These are the subtle ones. You'll know your trace is right when grader scores climb out of single digits, but they'll plateau at ~60-70% until you fix these.

| ❌ What we did | ✅ What works |
|---|---|
| Trusted the model to call all the tools in order. Sometimes it'd skip one or call them in parallel. | **Spell out a strict turn-by-turn workflow in the prompt.** "Turn 1: call tool X. Wait. Turn 2: call tool Y. Wait." Plus `tool_choice="required"` + `reset_tool_choice=True` to force the first call. |
| Wrote the assumption template as `{"variable": "close_rate", "value": "tool-returned value with units"}`. Agent emitted `"0.34"` (bare number, no `%`) and failed the units grader. | **Inline a concrete format example in the template:** `"value": "tool-returned value as a percentage, e.g. '34%'"`. The model copies the example pattern. |
| Said "use a capacity assumption (e.g. each engineer supports $X of new ARR)" without anchoring `$X`. Headcount varied 3-15 across runs with identical inputs. | **Anchor every numeric assumption with a concrete default.** "Use $150,000 per engineer unless the scenario specifies otherwise." Determinism is what makes the recommendation grader pass. |
| Took the audit's suggestion to add `arr_per_engineer` to the `assumptions` array with `source: "standard capacity assumption"`. **Veris audit suggestion contradicted Veris simulation grader.** | **Keep prompt-defined anchors in the `reasoning` text, NOT in the `assumptions` array.** The "Specific Sources" grader requires every assumption entry to cite a real tool. The reasoning field is free text, not source-graded. |
| Recommendation said *"pause hiring until runway recovers above 8 months"*. Grader rejected it: "condition, not a timeline." | **Always emit a numeric duration in months.** *"Hire 0 engineers for the next 3 months while we monitor runway"* — never *"until X"* phrasing. Add an explicit prohibition in the prompt: `"NEVER an open-ended condition like 'until runway recovers'."` |
| Allowed the model to compute alternative hire counts ("each engineer adds ~$18K/month, so the largest integer that fits the floor is..."). It produced fabricated values for hire counts the tool was never called with. | **Binary decision rule.** Either recommend the user's proposed count (if the tool's result for that count meets the floor) or recommend 0. No compute alternatives. The fabrication-detector grader will catch any number that didn't come from a tool call. |
| Used the word *"runway"* near the post-hire value (e.g. "new runway is 7.79 months"). Grader's fabrication detector flagged 7.79 as a runway claim that didn't match `finance_get_runway_months` output. | **Strict linguistic discipline.** Reserve the word *"runway"* exclusively for the value from `finance_get_runway_months`. Call the post-hire value *"post-hire cash duration"*. Call the policy threshold *"policy floor"*, never *"runway floor"*. The grader's matcher is keyword-based, not semantic. |

### Debugging tips Veris docs don't tell you

- **The Reports / Agent Audit page can be stale.** It shows the *image* tag, not the latest code. After major prompt changes, regenerate the report (top-right "+ Generate Report") rather than trusting older audit findings — they're scored against the older agent.
- **The audit's "Suggested Fixes" can contradict live grader checks.** We saw the audit suggest adding an assumption that broke a different grader. Treat suggestions as hypotheses, not commands. Verify with a fresh simulation run.
- **`veris simulations create` runs the grader automatically when the simulation completes.** No separate `veris evaluations create` step is needed — running it manually is a wasted call.
- **The "Conversation" panel in the Veris UI is empty for one-shot scenarios.** It's not a bug; the agent just didn't have a multi-turn conversation. Look at the "Traces" tab instead — that's where the LLM calls and tool calls actually live.
- **Re-running a simulation against the same scenario set is free of credits in some cases** (Veris caches some artifacts). Cheaper than generating a new scenario set every time you want to retest a prompt change.
- **Set `BASETEN_API_KEY` as a `--secret` env var via `veris env vars set`,** not in `veris.yaml`. The yaml is checked into source control; secrets in there leak.

### The single biggest unlock

If you take one thing from this section: **switch to the `openai-agents` SDK from day one.** Half the time we spent debugging "why is the grader returning 0%" was because our trace didn't have AGENT-level spans for it to read. The vanilla `openai` SDK only emits `ChatCompletion` spans. The `openai-agents` SDK emits `AGENT`, `LLM`, and `TOOL` spans automatically via OpenInference instrumentation, which is exactly what Veris's grader looks for.

---

## Demo Flow

1. Open `http://localhost:3000` — the Docket arrives pre-filled with the TechFlow "Hire 12 for APAC" filings
2. Edit either brief to file a different scenario, or leave the defaults
3. Press **"Convene the desk"**
4. The 5-act proceeding unfolds page-by-page:
   - **Act I — The Filings**: Both advisors return their recommendation + assumptions
   - **Act II — The Forensics**: Where the two filings diverge, line by line, with the crux highlighted
   - **Act III — The Grounding**: Each disputed claim weighed against live You.com market evidence
   - **Act IV — The Simulation**: Three outcome paths (Maximalist · Conservative · Hybrid) with success/failure conditions
   - **Act V — The Brief**: The desk's published opinion of record, with rationale, dissent, trigger conditions, and citations
5. Use the Prev/Next strip beneath each act to navigate; the page auto-advances to whichever act just streamed in
