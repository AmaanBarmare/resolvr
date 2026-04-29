# Resolvr

> Multi-agent conflict arbitration — when your AIs disagree, who decides?

Built for **Enterprise Agent Jam NYC 2026** · Target awards: Veris Achievement + Most Creative

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
| Frontend | Next.js 14 (React 18) + custom editorial CSS |
| Backend | FastAPI (Python 3.11) |
| LLM Inference | Baseten (Claude claude-sonnet-4-5) |
| Agent Sandbox | Veris AI (CLI — pre-run before demo) |
| Market Grounding | You.com Search API |
| Storage | Local JSON files (pre-saved Veris transcripts) |
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
│   │   └── transcript_b.json         # Pre-saved Veris transcript (Agent B)
│   └── requirements.txt
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

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
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

## The Critical Veris Note

Veris has **no REST API**. It is CLI-only. You cannot trigger a Veris simulation from the "Convene the desk" button.

**What to do instead:** Pre-run Veris the morning of the demo. Save the transcripts. With `USE_MOCK_PIPELINE=true` the pipeline replays those transcripts instantly through Stages 2–5 live.

See [VERIS_SETUP.md](VERIS_SETUP.md) for the full pre-run guide.

---

## Demo Flow

1. Open `http://localhost:3000`
2. The Docket arrives pre-filled with the TechFlow "Hire 12 for APAC" filings — edit either brief or leave the defaults
3. Press **"Convene the desk"**
4. Watch 5 stages stream in:
   - Stage 1: Revenue and Risk advisors run live → two recommendation cards appear
   - Stage 2: Forensics runs → divergence table renders, conflicting row highlights red
   - Stage 3: You.com fires → verdict status + source links snap in
   - Stage 4: Simulation runs → 3 path cards appear (Hybrid highlighted)
   - Stage 5: Brief generates → decision card with recommendation + dissent

Total demo time including pitch: 3 minutes.
