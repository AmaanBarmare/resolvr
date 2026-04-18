'use client';
import React from 'react';

interface Props {
  running: boolean;
  finished: boolean;
  hasResults: boolean;
  onRun: () => void;
}

/**
 * Docket — the case sheet. Sets the conflict, frames the proceeding,
 * and holds the primary call-to-action. This is the hero element.
 */
export function Docket({ running, finished, hasResults, onRun }: Props) {
  return (
    <section
      style={{
        position: 'relative',
        background: 'var(--paper-bright)',
        border: '0.5px solid var(--ink-rule-strong)',
        padding: '32px 36px 28px',
        display: 'grid',
        gridTemplateColumns: '1fr 320px',
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
          Two AI advisors examined the same balance sheet, the same pipeline, the same six-month
          window — and arrived at directly opposed counsel. The Revenue agent demands twelve
          immediate hires. The Risk agent demands a complete freeze.{' '}
          <span style={{ color: 'var(--ink)', fontWeight: 500 }}>
            Resolvr finds where the reasoning split, weighs the disputed numbers against live
            market evidence, and issues a published opinion.
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

      {/* RIGHT — action panel */}
      <div
        style={{
          background: 'var(--ink)',
          color: 'var(--paper-bright)',
          padding: '24px 22px 20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
        }}
      >
        <div>
          <div
            className="eyebrow-tight"
            style={{ color: 'var(--paper-deep)', marginBottom: 10, opacity: 0.75 }}
          >
            Proceeding
          </div>
          <div
            className="serif"
            style={{
              fontSize: 19,
              lineHeight: 1.35,
              fontStyle: 'italic',
              marginBottom: 18,
              color: 'var(--paper-bright)',
            }}
          >
            The desk will hear both filings, locate the divergence, ground every disputed claim
            against the market, simulate outcomes, and publish a brief.
          </div>

          {/* Mini timeline preview */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: 6,
              marginBottom: 22,
            }}
          >
            {['Filings', 'Forensics', 'Grounding', 'Simulation', 'Brief'].map((s, i) => (
              <div key={s} style={{ textAlign: 'center' }}>
                <div
                  className="mono"
                  style={{
                    fontSize: 9,
                    color: 'var(--paper-deep)',
                    opacity: 0.7,
                    marginBottom: 4,
                  }}
                >
                  0{i + 1}
                </div>
                <div
                  className="eyebrow-tight"
                  style={{ fontSize: 8.5, color: 'var(--paper-bright)', letterSpacing: '0.1em' }}
                >
                  {s}
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={onRun}
          disabled={running}
          style={{
            width: '100%',
            background: running
              ? 'transparent'
              : finished
                ? 'var(--forest-paper)'
                : 'var(--paper-bright)',
            color: running
              ? 'var(--paper-deep)'
              : finished
                ? 'var(--forest-ink)'
                : 'var(--ink)',
            border: running ? '0.5px solid var(--paper-deep)' : 'none',
            padding: '14px 16px',
            fontFamily: 'var(--font-sans)',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            cursor: running ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            transition: 'transform 0.18s, background 0.2s',
          }}
          onMouseEnter={(e) => {
            if (!running && !finished) (e.currentTarget.style.transform = 'translateY(-1px)');
          }}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          {running ? (
            <>
              <span className="spin" />
              The desk is in session
            </>
          ) : finished ? (
            <>
              ✓ Verdict on file &nbsp;·&nbsp; Re-hear case
            </>
          ) : hasResults ? (
            <>
              Re-open the case &nbsp;→
            </>
          ) : (
            <>
              Convene the desk &nbsp;→
            </>
          )}
        </button>

        <div
          className="eyebrow-tight"
          style={{
            color: 'var(--paper-deep)',
            opacity: 0.65,
            marginTop: 10,
            fontSize: 8.5,
            textAlign: 'center',
          }}
        >
          ~16 sec · 5 stages · Live market grounding
        </div>
      </div>
    </section>
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
