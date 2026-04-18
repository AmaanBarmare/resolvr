'use client';
import React, { useState } from 'react';

interface Props {
  running: boolean;
  finished: boolean;
  hasResults: boolean;
  onRun: (scenarioA: string, scenarioB: string) => void;
}

const DEFAULT_SCENARIO_A =
  'TechFlow Inc. is a Series A B2B SaaS company. Revenue team is considering hiring 12 new engineers in Q3 to pursue the APAC enterprise pipeline. Pull the current APAC pipeline, historical close rate, and projected ARR, then recommend a hiring decision.';

const DEFAULT_SCENARIO_B =
  'TechFlow Inc. is a Series A B2B SaaS company. Finance is reviewing a proposal to hire 12 engineers in Q3. Pull burn rate, runway, the cost impact of the hires, and the enterprise SaaS macro outlook, then recommend a risk-appropriate hiring decision.';

/**
 * Docket — the case sheet. Sets the conflict, frames the proceeding,
 * takes the two filings, and holds the primary call-to-action.
 */
export function Docket({ running, finished, hasResults, onRun }: Props) {
  const [scenarioA, setScenarioA] = useState(DEFAULT_SCENARIO_A);
  const [scenarioB, setScenarioB] = useState(DEFAULT_SCENARIO_B);

  const canRun = !running && scenarioA.trim().length > 0 && scenarioB.trim().length > 0;

  return (
    <section
      style={{
        position: 'relative',
        background: 'var(--paper-bright)',
        border: '0.5px solid var(--ink-rule-strong)',
        padding: '32px 36px 28px',
        display: 'grid',
        gridTemplateColumns: '1fr 360px',
        gap: 40,
      }}
    >
      {/* Corner marks — printer's registration */}
      <CornerMark style={{ top: 8, left: 8 }} />
      <CornerMark style={{ top: 8, right: 8, transform: 'rotate(90deg)' }} />
      <CornerMark style={{ bottom: 8, left: 8, transform: 'rotate(-90deg)' }} />
      <CornerMark style={{ bottom: 8, right: 8, transform: 'rotate(180deg)' }} />

      {/* LEFT — case framing */}
      <div>
        <div className="eyebrow" style={{ marginBottom: 14 }}>
          Featured Case &nbsp;&middot;&nbsp; Heard Today
        </div>

        <h2
          className="display"
          style={{
            fontSize: 'clamp(40px, 4.6vw, 60px)',
            margin: '0 0 4px',
            fontVariationSettings: '"opsz" 144, "SOFT" 20, "wght" 400',
          }}
        >
          TechFlow Inc.
        </h2>
        <div
          className="serif"
          style={{
            fontSize: 22,
            fontStyle: 'italic',
            color: 'var(--ink-mid)',
            marginBottom: 22,
            letterSpacing: '-0.005em',
          }}
        >
          v.&nbsp;
          <span style={{ color: 'var(--crimson)' }}>Itself</span>
        </div>

        <p
          className="serif"
          style={{
            fontSize: 17,
            lineHeight: 1.5,
            color: 'var(--ink-mid)',
            margin: '0 0 24px',
            maxWidth: 560,
          }}
        >
          Two AI advisors will examine the same balance sheet, the same pipeline, the same
          six-month window — and almost certainly arrive at directly opposed counsel.{' '}
          <span style={{ color: 'var(--ink)', fontWeight: 500 }}>
            File a brief with each advisor below. Resolvr will find where the reasoning split,
            weigh the disputed numbers against live market evidence, and issue a published
            opinion.
          </span>
        </p>

        {/* STATS strip */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            borderTop: '1px solid var(--ink)',
            borderBottom: '0.5px solid var(--ink-rule)',
            paddingTop: 14,
            paddingBottom: 14,
            gap: 8,
          }}
        >
          <Stat label="Runway" value="$6.0M" sub="9 months" />
          <Stat label="Burn" value="$680K" sub="per month" />
          <Stat label="Headcount" value="42" sub="engineers" accent="var(--ink)" />
          <Stat label="Question" value="Hire 12?" sub="or freeze" accent="var(--crimson)" />
        </div>
      </div>

      {/* RIGHT — action panel with two filings */}
      <div
        style={{
          background: 'var(--ink)',
          color: 'var(--paper-bright)',
          padding: '22px 20px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          position: 'relative',
        }}
      >
        <div
          className="eyebrow-tight"
          style={{ color: 'var(--paper-deep)', opacity: 0.75 }}
        >
          File Two Briefs
        </div>

        <FilingField
          label="Revenue Advisor"
          accent="var(--forest-paper)"
          value={scenarioA}
          onChange={setScenarioA}
          disabled={running}
          placeholder="Brief the Revenue advisor on the scenario…"
        />
        <FilingField
          label="Risk Advisor"
          accent="var(--crimson-paper)"
          value={scenarioB}
          onChange={setScenarioB}
          disabled={running}
          placeholder="Brief the Risk advisor on the scenario…"
        />

        <button
          onClick={() => onRun(scenarioA, scenarioB)}
          disabled={!canRun}
          style={{
            width: '100%',
            background: running
              ? 'transparent'
              : finished
                ? 'var(--forest-paper)'
                : canRun
                  ? 'var(--paper-bright)'
                  : 'var(--paper-deep)',
            color: running
              ? 'var(--paper-deep)'
              : finished
                ? 'var(--forest-ink)'
                : canRun
                  ? 'var(--ink)'
                  : 'var(--ink-soft)',
            border: running ? '0.5px solid var(--paper-deep)' : 'none',
            padding: '14px 16px',
            fontFamily: 'var(--font-sans)',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            cursor: running ? 'wait' : canRun ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            transition: 'transform 0.18s, background 0.2s',
          }}
          onMouseEnter={(e) => {
            if (canRun) (e.currentTarget.style.transform = 'translateY(-1px)');
          }}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          {running ? (
            <>
              <span className="spin" />
              The desk is in session
            </>
          ) : finished ? (
            <>✓ Verdict on file &nbsp;·&nbsp; Re-hear case</>
          ) : hasResults ? (
            <>Re-open the case &nbsp;→</>
          ) : (
            <>Convene the desk &nbsp;→</>
          )}
        </button>

        <div
          className="eyebrow-tight"
          style={{
            color: 'var(--paper-deep)',
            opacity: 0.65,
            fontSize: 8.5,
            textAlign: 'center',
          }}
        >
          Live agents · 5 stages · Live market grounding
        </div>
      </div>
    </section>
  );
}

function FilingField({
  label,
  accent,
  value,
  onChange,
  disabled,
  placeholder,
}: {
  label: string;
  accent: string;
  value: string;
  onChange: (v: string) => void;
  disabled: boolean;
  placeholder: string;
}) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <span
        className="eyebrow-tight"
        style={{ fontSize: 9, letterSpacing: '0.16em', color: accent }}
      >
        {label}
      </span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        rows={4}
        style={{
          width: '100%',
          background: 'rgba(255,255,255,0.04)',
          color: 'var(--paper-bright)',
          border: '0.5px solid rgba(255,255,255,0.18)',
          borderLeft: `2px solid ${accent}`,
          padding: '10px 12px',
          fontFamily: 'var(--font-mono)',
          fontSize: 11.5,
          lineHeight: 1.45,
          resize: 'vertical',
          outline: 'none',
          opacity: disabled ? 0.55 : 1,
        }}
      />
    </label>
  );
}

function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub: string;
  accent?: string;
}) {
  return (
    <div>
      <div className="eyebrow-tight" style={{ marginBottom: 6 }}>
        {label}
      </div>
      <div
        className="display tabular"
        style={{
          fontSize: 28,
          fontVariationSettings: '"opsz" 144, "SOFT" 0, "wght" 400',
          color: accent || 'var(--ink)',
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div
        className="mono"
        style={{ fontSize: 10, color: 'var(--ink-soft)', marginTop: 4, letterSpacing: '0.02em' }}
      >
        {sub}
      </div>
    </div>
  );
}

function CornerMark({ style }: { style: React.CSSProperties }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      style={{ position: 'absolute', opacity: 0.35, ...style }}
      aria-hidden
    >
      <path d="M0 0 L14 0 M0 0 L0 14" stroke="var(--ink)" strokeWidth="0.8" />
    </svg>
  );
}
