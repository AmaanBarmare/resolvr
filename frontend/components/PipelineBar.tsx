'use client';
import React from 'react';

interface Props {
  activeStage: number | string | null;
  completedStages: number[];
}

const STAGES: { n: number; label: string; sub: string }[] = [
  { n: 1, label: 'Filings',    sub: 'Both agents enter recommendations' },
  { n: 2, label: 'Forensics',  sub: 'Locate assumption divergence' },
  { n: 3, label: 'Grounding',  sub: 'Verify against live market' },
  { n: 4, label: 'Simulation', sub: 'Project conditional outcomes' },
  { n: 5, label: 'Brief',      sub: 'Publish the decision' },
];

/**
 * Procedural Calendar — the 5 stages laid out as numbered acts in a docket.
 * No pills, no bubbles. Numbers, rules, and one moving thread.
 */
export function PipelineBar({ activeStage, completedStages }: Props) {
  return (
    <section
      style={{
        border: '0.5px solid var(--ink-rule-strong)',
        background: 'var(--paper-bright)',
      }}
    >
      {/* Eyebrow row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          padding: '10px 18px',
          borderBottom: '0.5px solid var(--ink-rule)',
          alignItems: 'baseline',
        }}
      >
        <span className="eyebrow">Procedural Calendar</span>
        <span className="eyebrow-tight" style={{ color: 'var(--ink-soft)' }}>
          {completedStages.length}/5 acts complete
        </span>
      </div>

      {/* Stage grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          position: 'relative',
        }}
      >
        {/* horizontal connecting thread */}
        <div
          style={{
            position: 'absolute',
            top: 38,
            left: '10%',
            right: '10%',
            height: 1,
            background: 'var(--ink-rule)',
            zIndex: 0,
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: 38,
            left: '10%',
            width: `${(completedStages.length / 5) * 80}%`,
            height: 1,
            background: 'var(--ink)',
            zIndex: 1,
            transition: 'width 0.5s cubic-bezier(0.2, 0.7, 0.2, 1)',
          }}
        />

        {STAGES.map(({ n, label, sub }, i) => {
          const done = completedStages.includes(n);
          const active = activeStage === n;
          const future = !done && !active;

          const numColor = done
            ? 'var(--ink)'
            : active
              ? 'var(--crimson)'
              : 'var(--ink-faint)';

          return (
            <div
              key={n}
              style={{
                padding: '20px 14px 18px',
                borderLeft: i === 0 ? 'none' : '0.5px solid var(--ink-rule)',
                textAlign: 'center',
                position: 'relative',
                zIndex: 2,
                background: active ? 'var(--paper)' : 'transparent',
                transition: 'background 0.25s',
              }}
            >
              {/* The numeral — large, display serif */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  marginBottom: 10,
                  position: 'relative',
                }}
              >
                <span
                  className="display tabular"
                  style={{
                    fontSize: 32,
                    fontVariationSettings: done
                      ? '"opsz" 144, "SOFT" 0, "wght" 400'
                      : '"opsz" 144, "SOFT" 50, "wght" 300',
                    color: numColor,
                    background: 'var(--paper-bright)',
                    padding: '0 12px',
                    lineHeight: 1,
                    fontStyle: active ? 'italic' : 'normal',
                    transition: 'color 0.25s',
                  }}
                >
                  {String(n).padStart(2, '0')}
                </span>
                {active && (
                  <span
                    className="spin"
                    style={{
                      position: 'absolute',
                      right: 10,
                      top: 4,
                      color: 'var(--crimson)',
                    }}
                  />
                )}
                {done && !active && (
                  <span
                    style={{
                      position: 'absolute',
                      right: 14,
                      top: 6,
                      color: 'var(--forest)',
                      fontSize: 14,
                    }}
                  >
                    ✓
                  </span>
                )}
              </div>

              <div
                className="eyebrow"
                style={{
                  fontSize: 10,
                  letterSpacing: '0.18em',
                  color: future ? 'var(--ink-faint)' : 'var(--ink)',
                  marginBottom: 4,
                }}
              >
                {label}
              </div>
              <div
                className="serif"
                style={{
                  fontSize: 11.5,
                  fontStyle: 'italic',
                  color: future ? 'var(--ink-faint)' : 'var(--ink-soft)',
                  lineHeight: 1.35,
                  minHeight: 32,
                }}
              >
                {sub}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
