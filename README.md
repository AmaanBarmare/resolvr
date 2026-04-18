# Resolvr

> Multi-agent conflict arbitration — when your AIs disagree, who decides?

Built for **Enterprise Agent Jam NYC 2026** · Target awards: Veris Achievement + Most Creative

---

## What It Does

Enterprises run dozens of AI agents simultaneously. They constantly give conflicting outputs:

- Revenue agent says **"Hire 12 engineers now"**
- Risk agent says **"Freeze all headcount"**

Today there is zero infrastructure to resolve those conflicts.

**Resolvr** is the arbitration layer. It:

1. Takes two conflicting agent outputs (Veris behavioral transcripts)
2. Finds **exactly** where their reasoning diverged (Forensics Agent)
3. Verifies each disputed assumption against live market data (You.com)
4. Simulates what happens if you follow each path (Simulation Agent)
5. Produces a 1-page decision brief with a recommendation + dissenting opinion (Brief Agent)

The human executive still decides. We just make that decision defensible to their board.

---

## Demo Company — Pre-Seeded Data

All demo data is hardcoded in `backend/data/seed.json`. No user input needed.

| Field | Value |
|---|---|
| Company | TechFlow Inc. — B2B SaaS, Series A |
| Runway | $6M · $680K/month burn · ~9 months |
| Team | 42 engineers today |
| Pipeline | $4.2M potential ARR in APAC |
| Decision | Hire 12 engineers or freeze headcount? |
| **Agent A says** | Hire 12 — uses 34% close rate (internal CRM) |
| **Agent B says** | Freeze — uses 19% close rate (macro benchmark) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 + Tailwind CSS |
| Backend | FastAPI (Python 3.11) |
| LLM Inference | Baseten (Claude claude-sonnet-4-5) |
| Agent Sandbox | Veris AI (CLI — pre-run before demo) |
| Market Grounding | You.com Search API |
| Storage | Local JSON files (pre-saved Veris transcripts) |
| Streaming | Server-Sent Events (SSE) for live UI updates |

---

## Project Structure

```
divorce-lawyer/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── pipeline.py              # Full pipeline orchestrator (SSE stream)
│   ├── agents/
│   │   ├── revenue_agent.py     # Agent A — Revenue agent code
│   │   └── risk_agent.py        # Agent B — Risk agent code
│   ├── pipeline_stages/
│   │   ├── forensics.py         # Stage 2 — Assumption extraction
│   │   ├── grounding.py         # Stage 3 — You.com verification
│   │   ├── simulation.py        # Stage 4 — Outcome trees
│   │   └── brief.py             # Stage 5 — Decision brief
│   ├── data/
│   │   ├── seed.json            # TechFlow Inc. scenario data
│   │   ├── transcript_a.json    # Pre-saved Veris transcript (Agent A)
│   │   └── transcript_b.json    # Pre-saved Veris transcript (Agent B)
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Main dashboard page
│   │   └── api/run/route.ts     # SSE route proxy to backend
│   ├── components/
│   │   ├── PipelineBar.tsx      # 5-stage progress indicator
│   │   ├── AgentCards.tsx       # Side-by-side agent output cards
│   │   ├── DivergenceTable.tsx  # Assumption comparison table
│   │   ├── GroundingBadges.tsx  # You.com verdict badges
│   │   ├── PathCards.tsx        # 3 outcome path cards
│   │   └── BriefCard.tsx        # Final decision brief
│   └── package.json
├── veris/
│   ├── agent_a/
│   │   ├── Dockerfile
│   │   ├── veris.yaml
│   │   └── revenue_agent/
│   │       └── main.py
│   └── agent_b/
│       ├── Dockerfile
│       ├── veris.yaml
│       └── risk_agent/
│           └── main.py
├── docs/
│   ├── README.md                # This file
│   ├── CLAUDE.md                # Claude Code instructions
│   ├── ARCHITECTURE.md          # System architecture
│   ├── AGENTS.md                # How Agent A + B are built
│   ├── VERIS_SETUP.md           # Veris pre-run guide
│   ├── API.md                   # Backend API reference
│   └── PIPELINE.md              # Pipeline stages + prompts
└── .env.example
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

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

Veris has **no REST API**. It is CLI-only. You cannot trigger a Veris simulation from the "Run Arbitration" button.

**What to do instead:** Pre-run Veris the morning of the demo. Save the transcripts. The button then loads those transcripts instantly and runs Stages 2–5 live.

See `docs/VERIS_SETUP.md` for the full pre-run guide.

---

## Demo Flow

1. Open `http://localhost:3000`
2. Press **"Run Arbitration"**
3. Watch 5 stages complete in ~18 seconds:
   - Stage 1: Agent transcripts load → two recommendation cards appear
   - Stage 2: Forensics runs → divergence table renders, conflicting row highlights red
   - Stage 3: You.com fires → verdict badges snap in with source links
   - Stage 4: Simulation runs → 3 path cards appear (Hybrid highlighted green)
   - Stage 5: Brief generates → decision card with recommendation + dissent

Total demo time including pitch: 3 minutes.
