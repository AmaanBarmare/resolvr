'use client';
import React from 'react';
import { SectionHeader } from './SectionHeader';

interface Row {
  variable: string;
  agent_a_value: string;
  agent_a_source: string;
  agent_b_value: string;
  agent_b_source: string;
  divergence_type: 'data_conflict' | 'missing_var' | 'horizon_mismatch' | 'agreed';
  is_crux: boolean;
}

interface GroundedRow {
  variable: string;
  market_benchmark: string;
  verdict: 'outlier' | 'aligned' | 'unverifiable';
  source_url: string;
  source_name: string;
}

interface Props {
  data: { assumption_table: Row[]; finding: string; crux_variable: string };
  grounded?: Record<string, GroundedRow>;
}

const TYPE_TAG: Record<Row['divergence_type'], { label: string; color: string }> = {
  data_conflict:    { label: 'Conflict',  color: 'var(--crimson-ink)' },
  missing_var:      { label: 'Missing',   color: 'var(--amber-ink)' },
  horizon_mismatch: { label: 'Horizon',   color: 'var(--amber-ink)' },
  agreed:           { label: 'Stipulated', color: 'var(--forest-ink)' },
};

const VERDICT_TAG: Record<string, { label: string; color: string; bg: string }> = {
  outlier:      { label: 'Outlier',      color: 'var(--crimson-ink)', bg: 'var(--crimson-paper)' },
  aligned:      { label: 'Aligned',      color: 'var(--forest-ink)',  bg: 'var(--forest-paper)' },
  unverifiable: { label: 'Unverifiable', color: 'var(--ink-soft)',    bg: 'var(--paper-deep)' },
};

export function DivergenceTable({ data, grounded }: Props) {
  return (
    <section className="section">
      <SectionHeader
        stage={2}
        description="Where the two filings diverge, line by line."
        meta={`${data.assumption_table.length} assumptions on ledger`}
      />

      {/* The Crux — featured callout (stacked so long variable names never overlap the finding) */}
      <div
        style={{
          background: 'var(--ink)',
          color: 'var(--paper-bright)',
          padding: '20px 24px 22px',
          marginBottom: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          borderBottom: '4px double var(--ink)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
          <span
            className="eyebrow-tight"
            style={{ color: 'var(--paper-deep)', opacity: 0.7, whiteSpace: 'nowrap' }}
          >
            The Crux
          </span>
          <span
            className="mono"
            style={{
              flex: 1,
              fontSize: 22,
              color: 'var(--paper-bright)',
              fontStyle: 'italic',
              lineHeight: 1.1,
              wordBreak: 'break-word',
              fontVariationSettings: '"opsz" 144, "SOFT" 20, "wght" 400',
            }}
          >
            {data.crux_variable}
          </span>
        </div>
        <p
          className="serif"
          style={{
            margin: 0,
            fontSize: 16,
            lineHeight: 1.5,
            color: 'var(--paper-bright)',
            fontStyle: 'italic',
          }}
        >
          {data.finding}
        </p>
      </div>

      {/* Ledger */}
      <div style={{ background: 'var(--paper-bright)', border: '0.5px solid var(--ink-rule-strong)', borderTop: 'none' }}>
        {/* Header row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.5fr 1.2fr 1.2fr 0.9fr 1.4fr',
            padding: '10px 18px',
            borderBottom: '1px solid var(--ink)',
            background: 'var(--paper-deep)',
            gap: 12,
          }}
        >
          {['Variable', 'Petitioner', 'Respondent', 'Nature', 'Market Verdict'].map((h) => (
            <div key={h} className="eyebrow-tight" style={{ color: 'var(--ink-mid)' }}>
              {h}
            </div>
          ))}
        </div>

        {data.assumption_table.map((r, i) => {
          const isCrux = r.is_crux;
          const gr = grounded?.[r.variable];
          const verdict = gr ? VERDICT_TAG[gr.verdict] : null;
          const isMissing = r.divergence_type === 'missing_var';

          return (
            <div
              key={r.variable}
              style={{
                display: 'grid',
                gridTemplateColumns: '1.5fr 1.2fr 1.2fr 0.9fr 1.4fr',
                padding: '14px 18px',
                borderBottom:
                  i === data.assumption_table.length - 1
                    ? 'none'
                    : '0.5px solid var(--ink-rule)',
                gap: 12,
                alignItems: 'center',
                position: 'relative',
                background: isCrux ? 'rgba(148, 34, 28, 0.04)' : 'transparent',
              }}
            >
              {isCrux && (
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: 3,
                    background: 'var(--crimson)',
                  }}
                />
              )}

              {/* Variable */}
              <div>
                <div
                  className="mono"
                  style={{
                    fontSize: 12.5,
                    fontWeight: isCrux ? 600 : 500,
                    color: isCrux ? 'var(--crimson)' : 'var(--ink)',
                  }}
                >
                  {r.variable}
                </div>
                {isCrux && (
                  <div
                    className="eyebrow-tight"
                    style={{ color: 'var(--crimson)', marginTop: 3, fontSize: 8.5 }}
                  >
                    ★ Crux of the proceeding
                  </div>
                )}
              </div>

              {/* Petitioner value */}
              <div>
                <div
                  className="mono tabular"
                  style={{
                    fontSize: 13.5,
                    fontWeight: 500,
                    color: r.agent_a_value === 'not modeled' ? 'var(--ink-faint)' : 'var(--amber-ink)',
                    fontStyle: r.agent_a_value === 'not modeled' ? 'italic' : 'normal',
                  }}
                >
                  {r.agent_a_value}
                </div>
                <div
                  className="mono"
                  style={{
                    fontSize: 9.5,
                    color: 'var(--ink-soft)',
                    marginTop: 2,
                  }}
                >
                  {r.agent_a_source}
                </div>
              </div>

              {/* Respondent value */}
              <div>
                <div
                  className="mono tabular"
                  style={{
                    fontSize: 13.5,
                    fontWeight: 500,
                    color: r.agent_b_value === 'not modeled' ? 'var(--ink-faint)' : 'var(--slate-ink)',
                    fontStyle: r.agent_b_value === 'not modeled' ? 'italic' : 'normal',
                  }}
                >
                  {r.agent_b_value}
                </div>
                <div
                  className="mono"
                  style={{
                    fontSize: 9.5,
                    color: 'var(--ink-soft)',
                    marginTop: 2,
                  }}
                >
                  {r.agent_b_source}
                </div>
              </div>

              {/* Nature */}
              <div>
                <span
                  className="eyebrow-tight"
                  style={{
                    color: TYPE_TAG[r.divergence_type].color,
                    fontSize: 9.5,
                    letterSpacing: '0.16em',
                  }}
                >
                  {isMissing && '◇ '}
                  {r.divergence_type === 'data_conflict' && '◆ '}
                  {r.divergence_type === 'agreed' && '◯ '}
                  {TYPE_TAG[r.divergence_type].label}
                </span>
              </div>

              {/* Market Verdict */}
              <div>
                {verdict ? (
                  <div>
                    <span
                      className="tag tag-solid"
                      style={{
                        background: verdict.bg,
                        color: verdict.color,
                      }}
                    >
                      {verdict.label}
                    </span>
                    {gr!.market_benchmark && gr!.market_benchmark !== 'unavailable' && (
                      <div
                        className="mono"
                        style={{ fontSize: 10, color: 'var(--ink-mid)', marginTop: 5 }}
                      >
                        Market: <span style={{ color: 'var(--ink)' }}>{gr!.market_benchmark}</span>
                      </div>
                    )}
                    {gr!.source_url && (
                      <a
                        href={gr!.source_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          fontSize: 10,
                          marginTop: 4,
                          display: 'inline-block',
                          fontStyle: 'italic',
                          fontFamily: 'var(--font-serif)',
                        }}
                      >
                        {gr!.source_name} ↗
                      </a>
                    )}
                  </div>
                ) : r.divergence_type === 'agreed' ? (
                  <span
                    className="serif"
                    style={{ color: 'var(--ink-faint)', fontSize: 12, fontStyle: 'italic' }}
                  >
                    no contest
                  </span>
                ) : (
                  <span className="eyebrow-tight" style={{ color: 'var(--ink-faint)' }}>
                    Pending
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
