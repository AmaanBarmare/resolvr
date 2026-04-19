'use client';
import React, { useState } from 'react';

interface Props {
  running: boolean;
  finished: boolean;
  hasResults: boolean;
  onRun: (scenarioA: string, scenarioB: string) => void;
}

const COMPANY_REV = 'TechFlow — Series A B2B SaaS, 42 engineers, $6M cash.';
const COMPANY_RSK = 'TechFlow — Series A B2B SaaS, $6M cash at $680K/mo burn.';

const DEFAULT_A = `${COMPANY_REV} Should we hire 12 engineers this quarter to deliver on the APAC pipeline? Give me the revenue math.`;
const DEFAULT_B = `${COMPANY_RSK} Can we absorb 12 new engineers this quarter without wrecking runway? Give me the risk read.`;
const SAMPLE_SUMMARY = 'Should we hire 12 engineers now to chase the APAC pipeline?';

/**
 * Docket — the case sheet. Context framing, two filings, and the primary CTA.
 */
export function Docket({ running, finished, hasResults, onRun }: Props) {
  const [scenarioA, setScenarioA] = useState(DEFAULT_A);
  const [scenarioB, setScenarioB] = useState(DEFAULT_B);

  const resetSample = () => {
    setScenarioA(DEFAULT_A);
    setScenarioB(DEFAULT_B);
  };

  const canRun = !running && scenarioA.trim().length > 0 && scenarioB.trim().length > 0;

  return (
    <section
      style={{
        position: 'relative',
        background: 'var(--paper-bright)',
        border: '0.5px solid var(--ink-rule-strong)',
        padding: '32px 36px 28px',
        display: 'grid',
        gridTemplateColumns: '1fr 380px',
        gap: 40,
      }}
    >
      <CornerMark style={{ top: 8, left: 8 }} />
      <CornerMark style={{ top: 8, right: 8, transform: 'rotate(90deg)' }} />
      <CornerMark style={{ bottom: 8, left: 8, transform: 'rotate(-90deg)' }} />
      <CornerMark style={{ bottom: 8, right: 8, transform: 'rotate(180deg)' }} />

      {/* LEFT — framing + sample picker */}
      <div>
        <div className="eyebrow" style={{ marginBottom: 14 }}>
          Today&apos;s Docket &nbsp;&middot;&nbsp; Open for Filing
        </div>

        <h2
          className="display"
          style={{
            fontSize: 'clamp(40px, 4.6vw, 60px)',
            margin: '0 0 8px',
            fontVariationSettings: '"opsz" 144, "SOFT" 20, "wght" 400',
          }}
        >
          Two advisors.
          <br />
          <span style={{ fontStyle: 'italic', color: 'var(--crimson)' }}>One verdict.</span>
        </h2>

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
          File any startup decision with both advisors. The Revenue desk presses the growth case;
          the Risk desk presses the runway case.{' '}
          <span style={{ color: 'var(--ink)', fontWeight: 500 }}>
            Resolvr synthesizes a case profile from your two briefs, runs both advisors live,
            locates where their reasoning split, grounds each disputed claim against live market
            evidence, and publishes a signed opinion.
          </span>
        </p>

        {/* FEATURED CASE */}
        <div style={{ borderTop: '1px solid var(--ink)', paddingTop: 14 }}>
          <div
            className="eyebrow-tight"
            style={{ marginBottom: 10, color: 'var(--ink-mid)' }}
          >
            Featured Case &nbsp;·&nbsp; Edit either brief to customize
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
            <button
              onClick={resetSample}
              disabled={running}
              style={{
                background: 'var(--ink)',
                color: 'var(--paper-bright)',
                border: '0.5px solid var(--ink)',
                padding: '8px 14px',
                fontFamily: 'var(--font-sans)',
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                cursor: running ? 'not-allowed' : 'pointer',
              }}
            >
              Hire 12 for APAC
            </button>
            <span
              className="serif"
              style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--ink-soft)' }}
            >
              {SAMPLE_SUMMARY}
            </span>
          </div>
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
          Live agents · Live market grounding · 5 stages
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
        rows={5}
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
