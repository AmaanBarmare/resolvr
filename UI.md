# UI.md — Premium Frontend Design

The UI is a single page. One "Run Arbitration" button. Five sections expand in sequence as each pipeline stage completes.

---

## Clarifying the Veris Flow

Veris outputs **JSON transcripts** — NOT PDFs. The complete flow:

```
1. You write Agent A + Agent B as Python code
2. veris env push  →  both agents uploaded to Veris cloud
3. veris run       →  Veris runs agents in isolated sandboxes
4. Veris produces  →  transcript_a.json + transcript_b.json
5. Save those files to  backend/data/
6. Button press    →  backend reads JSONs, streams pipeline to UI
7. 5 stages run    →  each one streams output to the UI as it completes
8. Final brief     →  renders as a premium styled card in the browser
```

No PDFs anywhere. The brief is a styled HTML card in the UI.

---

## Design Principles

- Flat surfaces. No gradients, no shadows, no glow.
- 0.5px borders everywhere — except the recommended path card (2px green border, the only exception).
- Every section fades up with a 220ms ease-out animation on mount.
- Color encodes meaning: amber = Agent A, blue = Agent B, teal = analysis, green = success/recommendation, red = divergence/outlier.
- Monospace font (`var(--font-mono)`) for all numbers, variable names, and source identifiers.

---

## Component Tree

```
page.tsx
├── <TopBar />
│     company chip | "Run Arbitration" button
├── <PipelineBar />
│     5 pills: Agents · Forensics · Grounding · Simulation · Brief
│     States: default → active (spinner) → done (checkmark)
│
└── Sections (each mounts as its stage completes)
      <AgentCards />        stage 1
      <DivergenceTable />   stage 2 (verdict column updates at stage 3)
      <GroundingStatus />   stage 3 status bar only
      <PathCards />         stage 4
      <BriefCard />         stage 5
```

---

## TopBar

```
Left side:
  company-name: "TechFlow Inc." → 15px, font-weight:500
  company-meta: "$6M runway · $680K/mo burn · 42 engineers · Hire 12 or freeze?"
              → 12px, color:var(--color-text-tertiary)

Right side — button states:
  .idle    → bg:var(--color-text-primary), color:var(--color-background-primary), text:"Run Arbitration"
  .running → disabled, bg:var(--color-background-secondary), border:0.5px, text:"Running..."
  .done    → bg:#27500A, color:#EAF3DE, text:"Arbitration complete"
```

---

## PipelineBar

```
Outer: bg:var(--color-background-secondary), border:0.5px, radius-lg, padding:4px
5 pills inside, each flex:1

Pill states:
  default → color:var(--color-text-tertiary), 6px dot icon
  active  → bg:var(--color-background-primary), border:0.5px solid var(--color-border-info)
             color:var(--color-text-info), 10px spinner icon
  done    → bg:var(--color-background-primary), border:0.5px solid var(--color-border-success)
             color:var(--color-text-success), 10px checkmark SVG icon

Labels: "Agents" | "Forensics" | "Grounding" | "Simulation" | "Brief"
Font: 11px, font-weight:500
```

---

## Section Header Pattern

Used by every stage section:

```tsx
<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
  <span class="section-tag">[Stage N]</span>
  <span style="font-size:13px;font-weight:500;color:var(--color-text-secondary)">
    [stage description]
  </span>
  <span style="font-size:11px;color:var(--color-text-tertiary);margin-left:auto">
    [right-aligned metadata]
  </span>
</div>
```

Section tag pill: `font-size:10px, font-weight:500, letter-spacing:0.05em, padding:3px 9px, border-radius:20px`

| Stage | Tag bg | Tag text |
|---|---|---|
| 1 | #FAEEDA | #633806 |
| 2 | #E1F5EE | #085041 |
| 3 | #E1F5EE | #085041 |
| 4 | #FAECE7 | #712B13 |
| 5 | #EAF3DE | #27500A |

---

## Stage 1 — Agent Cards

```
Grid: 2 columns, gap:10px

Agent A card:
  border-left: 3px solid #EF9F27 (amber-400)
  border-radius: var(--border-radius-lg)
  Header: label "AGENT A · REVENUE" (10px, #633806)
          rec "Hire 12 engineers now" (14px, font-weight:500)
  Body: assumption rows (variable | value)
        close_rate → value color #854F0B
        source → color:var(--color-text-tertiary)

Agent B card: mirror, border-left:3px solid #378ADD
  Header label color: #0C447C
  close_rate value color: #185FA5

Assumption row: display:flex, justify-content:space-between, padding:4px 0
  border-bottom: 0.5px solid var(--color-border-tertiary)
  variable: font-family:var(--font-mono), 11px, color:var(--color-text-tertiary)
  value: font-family:var(--font-mono), 11px
```

---

## Stage 2 — Divergence Table

```
Container: border:0.5px, radius-lg, overflow:hidden

Header row (bg:var(--color-background-secondary)):
  5 cols: Variable | Agent A | Agent B | Type | Verdict
  grid-template-columns: 1.4fr 1fr 1fr 1fr 1fr

Row types:
  close_rate (crux):
    background: var(--color-background-danger)
    variable: font-weight:500, color:var(--color-text-danger)
    Agent A value: color:#854F0B, font-weight:500
    Agent B value: color:#185FA5, font-weight:500
    type badge: "data conflict" → bg:#FCEBEB, color:#A32D2D

  macro_outlook (missing var):
    background: var(--color-background-warning)
    variable: font-weight:500, color:#633806
    type badge: "missing var" → bg:#FAEEDA, color:#633806

  agreed rows: default bg
    type badge: "agreed" → bg:#EAF3DE, color:#27500A

Verdict column (updated at Stage 3):
  initial: "—" gray pill
  OUTLIER: bg:#FCEBEB, color:#A32D2D + source link (color:var(--color-text-info))
  ALIGNED: bg:#EAF3DE, color:#27500A
  CONFIRMED: bg:#FCEBEB, color:#A32D2D + source link

Finding box (appears 200ms after table):
  background: var(--color-background-secondary)
  border-left: 3px solid var(--color-border-primary)
  border-radius: 0 radius-md radius-md 0
  padding: 9px 12px, font-size:12px, line-height:1.6
  animation: fadeup 0.2s ease-out
```

---

## Stage 3 — Grounding Status Bar

```
Loading state:
  10px spinner + "Querying You.com for enterprise SaaS benchmarks..."
  color: var(--color-text-tertiary), font-size:12px

Complete state (updates in place — no remount):
  checkmark SVG + "4 assumptions verified · 2 outliers found · sources cited"
  color: var(--color-text-success)

Simultaneously: verdict column in DivergenceTable gets updated values
  (component re-renders, no animation — badges just swap content)
```

---

## Stage 4 — Path Cards

```
Grid: 3 columns, gap:10px

Path A (red):
  header bg: #FCEBEB
  label: "PATH A" → 10px, color:#A32D2D
  name: "Hire 12 engineers" → 13px, font-weight:500
  description: 12px, color:var(--color-text-secondary), line-height:1.6
  trigger: border-top:0.5px, font-family:var(--font-mono), 11px, color:var(--color-text-danger)
           "Breaks if pipeline < $2.8M by Q3"

Path B (amber): mirror of A, header bg:#FAEEDA
  trigger color: var(--color-text-warning)

Hybrid — RECOMMENDED (green):
  border: 2px solid var(--color-border-success)  ← only 2px border in entire UI
  header bg: #EAF3DE
  label: "HYBRID · RECOMMENDED" → color:#27500A
  trigger color: var(--color-text-success)
  trigger text: "Trigger: Q3 pipeline > $3M ARR"
```

---

## Stage 5 — Brief Card

```
Container: border:0.5px, radius-lg, overflow:hidden, bg:var(--color-background-primary)

Header bar (bg:var(--color-background-secondary), padding:12px 16px):
  overline: "ARBITRATION BRIEF · TECHFLOW INC. · APRIL 18 2026"
            → 11px, font-weight:500, letter-spacing:0.05em, color:var(--color-text-tertiary)
  title: "APAC headcount decision — agent conflict resolved"
         → 13px, font-weight:500

Body: 2-column grid (1fr 1fr), border-left between columns

Section label style: 10px, font-weight:500, letter-spacing:0.06em,
                     color:var(--color-text-tertiary), margin-bottom:6px

LEFT COLUMN:
  RECOMMENDED DECISION
    green block: bg:var(--color-background-success), radius-md, padding:10px 12px
                 font-size:13px, font-weight:500, color:var(--color-text-success), line-height:1.5
                 "Hire 4 engineers now. Expand to 12 if Q3 pipeline closes above $3M ARR."

  RATIONALE
    plain text: 12px, color:var(--color-text-secondary), line-height:1.7

  DISSENTING OPINION
    amber block: bg:var(--color-background-warning), radius-md, padding:10px 12px
                 12px, color:var(--color-text-warning), line-height:1.6
                 "Agent B: Even 4 hires reduces runway to 7.8 months..."

RIGHT COLUMN:
  TRIGGER CONDITIONS (3 rows)
    Each: display:flex, gap:8px, padding:5px 0, border-bottom:0.5px
    number: "01"/"02"/"03" → 10px, font-weight:500, color:var(--color-text-tertiary), flex-shrink:0
    text: 12px, color:var(--color-text-secondary), line-height:1.4

  AUDIT LOG (3 rows)
    Each: display:flex, justify-content:space-between, padding:5px 0, border-bottom:0.5px
    claim: 12px, color:var(--color-text-secondary)
    source: 11px, color:var(--color-text-info), "Gartner 2026 ↗"
```

---

## Animation

```css
/* Every section uses this on mount */
@keyframes fadeup {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.section { animation: fadeup 0.22s ease-out; }

/* Spinner */
@keyframes spin { to { transform: rotate(360deg); } }
.spin {
  width: 10px; height: 10px;
  border: 1.5px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
```

---

## Timing (for demo pacing)

| Event | Seconds after button |
|---|---|
| Stage 1 complete | ~0.9s |
| Stage 2 complete | ~2.5s |
| Stage 3 loading | ~2.5s |
| Stage 3 complete + verdicts update | ~4.1s |
| Stage 4 complete | ~5.7s |
| Stage 5 complete | ~7.5s |
| Button turns green | ~7.5s |

Total: ~18 seconds. The judge watches the whole pipeline run in real time.

---

## SSE Hook

```typescript
// frontend/hooks/usePipeline.ts
import { useState, useCallback } from 'react'

export function usePipeline() {
  const [state, setState] = useState({
    running: false, activeStage: null, completedStages: [],
    loadingMessage: '', error: null, stageData: {}
  })

  const run = useCallback(() => {
    setState(s => ({ ...s, running: true, error: null }))
    const es = new EventSource('/api/run')

    es.onmessage = ({ data }) => {
      const e = JSON.parse(data)
      if (e.status === 'loading')
        setState(s => ({ ...s, activeStage: e.stage, loadingMessage: e.message }))
      if (e.status === 'complete' && e.stage !== 'done')
        setState(s => ({
          ...s,
          completedStages: [...s.completedStages, e.stage],
          stageData: { ...s.stageData, [e.stage]: e.data }
        }))
      if (e.stage === 'done') {
        setState(s => ({ ...s, running: false, activeStage: null }))
        es.close()
      }
    }

    es.onerror = () => {
      setState(s => ({ ...s, running: false, error: 'Connection lost' }))
      es.close()
    }
  }, [])

  return { state, run }
}
```

---

## Next.js SSE Proxy Route

```typescript
// frontend/app/api/run/route.ts
export async function GET() {
  const res = await fetch(`${process.env.BACKEND_URL}/api/run`, {
    headers: { Accept: 'text/event-stream' }
  })
  return new Response(res.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    }
  })
}
```
