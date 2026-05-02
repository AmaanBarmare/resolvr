'use client';
import React from 'react';
import { SectionHeader } from './SectionHeader';

type Verdict = 'outlier' | 'aligned' | 'unverifiable';

interface GroundedRow {
  variable: string;
  agent_a_value: string;
  agent_b_value: string;
  market_benchmark: string;
  verdict: Verdict;
  source_url: string;
  source_name: string;
  note: string;
}

interface Props {
  loading: boolean;
  loadingMessage?: string;
  grounded?: GroundedRow[];
}

const VERDICT_TAG: Record<Verdict, { label: string; color: string; bg: string; rule: string }> = {
  outlier:      { label: 'Outlier',      color: 'var(--crimson-ink)', bg: 'var(--crimson-paper)', rule: 'var(--crimson)' },
  aligned:      { label: 'Aligned',      color: 'var(--forest-ink)',  bg: 'var(--forest-paper)',  rule: 'var(--forest)' },
  unverifiable: { label: 'Unverifiable', color: 'var(--ink-soft)',    bg: 'var(--paper-deep)',    rule: 'var(--ink-rule-strong)' },
};

/**
 * Act III — The Grounding.
 *
 * A full standalone view of the per-assumption market verification:
 * each disputed/missing assumption gets its own row with the market
 * benchmark, verdict badge, source citation, and grader note.
 */
export function GroundingStatus({ loading, loadingMessage, grounded }: Props) {
  if (loading && !grounded) {
    return (
      <section className="section">
        <SectionHeader
          stage={3}
          description="Verifying every disputed claim against live market evidence."
          meta="On the wires"
        />
        <div
          style={{
            background: 'var(--paper-bright)',
            border: '0.5px solid var(--ink-rule-strong)',
            borderLeft: '3px solid var(--slate)',
            padding: '20px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <span className="spin" style={{ color: 'var(--slate)' }} />
          <span className="eyebrow-tight" style={{ color: 'var(--slate-ink)' }}>
            On the wires
          </span>
          <span style={{ flex: 1, height: 1, background: 'var(--ink-rule)' }} />
          <span
            className="serif"
            style={{ fontSize: 14, fontStyle: 'italic', color: 'var(--ink-mid)' }}
          >
            {loadingMessage || 'Querying You.com for market benchmarks…'}
          </span>
        </div>
      </section>
    );
  }

  if (!grounded) return null;

  const total = grounded.length;
  const outliers = grounded.filter((g) => g.verdict === 'outlier').length;
  const aligned = grounded.filter((g) => g.verdict === 'aligned').length;
  const unver = grounded.filter((g) => g.verdict === 'unverifiable').length;

  return (
    <section className="section">
      <SectionHeader
        stage={3}
        description="Each disputed claim, weighed against live market evidence."
        meta={`${total} ${total === 1 ? 'claim' : 'claims'} on the record`}
      />

      {/* Summary tally */}
      <div
        style={{
          background: 'var(--paper-bright)',
          border: '0.5px solid var(--ink-rule-strong)',
          borderLeft: '3px solid var(--forest)',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: 18,
          marginBottom: 0,
          borderBottom: 'none',
        }}
      >
        <span className="eyebrow-tight" style={{ color: 'var(--forest-ink)' }}>
          Grounding Returned
        </span>
        <span style={{ height: 18, width: 1, background: 'var(--ink-rule-strong)' }} />
        <Tally label="Verified" value={total} accent="var(--ink)" />
        <Tally label="Outliers" value={outliers} accent="var(--crimson)" />
        <Tally label="Aligned" value={aligned} accent="var(--forest)" />
        <Tally label="Unverifiable" value={unver} accent="var(--ink-soft)" />
        <span style={{ flex: 1 }} />
        <span
          className="serif"
          style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--ink-mid)' }}
        >
          Sources cited inline.
        </span>
      </div>

      {/* Per-assumption ledger */}
      <div
        style={{
          background: 'var(--paper-bright)',
          border: '0.5px solid var(--ink-rule-strong)',
          borderTop: 'none',
        }}
      >
        {grounded.map((g, i) => {
          const tag = VERDICT_TAG[g.verdict];
          const hasMarket = g.market_benchmark && g.market_benchmark !== 'unavailable';
          return (
            <div
              key={`${g.variable}-${i}`}
              style={{
                display: 'grid',
                gridTemplateColumns: '1.2fr 1.6fr 1.6fr',
                padding: '16px 22px',
                borderBottom:
                  i === grounded.length - 1 ? 'none' : '0.5px solid var(--ink-rule)',
                gap: 22,
                alignItems: 'flex-start',
                borderLeft: `3px solid ${tag.rule}`,
              }}
            >
              {/* Column 1 — variable + verdict */}
              <div>
                <div
                  className="mono"
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: 'var(--ink)',
                    marginBottom: 6,
                  }}
                >
                  {g.variable}
                </div>
                <span
                  className="tag tag-solid"
                  style={{
                    background: tag.bg,
                    color: tag.color,
                  }}
                >
                  {tag.label}
                </span>
              </div>

              {/* Column 2 — what each agent said */}
              <div>
                <div className="eyebrow-tight" style={{ color: 'var(--ink-mid)', marginBottom: 5 }}>
                  Filed Values
                </div>
                <div
                  className="mono tabular"
                  style={{ fontSize: 12, color: 'var(--amber-ink)', marginBottom: 3 }}
                >
                  Petitioner:{' '}
                  <span style={{ color: 'var(--ink)' }}>{g.agent_a_value || '—'}</span>
                </div>
                <div
                  className="mono tabular"
                  style={{ fontSize: 12, color: 'var(--slate-ink)' }}
                >
                  Respondent:{' '}
                  <span style={{ color: 'var(--ink)' }}>{g.agent_b_value || '—'}</span>
                </div>
              </div>

              {/* Column 3 — market evidence */}
              <div>
                <div className="eyebrow-tight" style={{ color: 'var(--ink-mid)', marginBottom: 5 }}>
                  Market Record
                </div>
                {hasMarket ? (
                  <div
                    className="mono tabular"
                    style={{ fontSize: 12.5, color: 'var(--ink)', marginBottom: 6, fontWeight: 500 }}
                  >
                    {g.market_benchmark}
                  </div>
                ) : (
                  <div
                    className="serif"
                    style={{ fontSize: 12, color: 'var(--ink-faint)', fontStyle: 'italic', marginBottom: 6 }}
                  >
                    No market record located.
                  </div>
                )}
                {g.note && (
                  <div
                    className="serif"
                    style={{ fontSize: 12.5, color: 'var(--ink-mid)', marginBottom: 6, lineHeight: 1.4 }}
                  >
                    {g.note}
                  </div>
                )}
                {g.source_url && (
                  <a
                    href={g.source_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: 11.5,
                      fontStyle: 'italic',
                      fontFamily: 'var(--font-serif)',
                      color: 'var(--ink-mid)',
                    }}
                  >
                    {g.source_name || g.source_url} ↗
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Tally({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
      <span
        className="display tabular"
        style={{
          fontSize: 22,
          color: accent,
          fontVariationSettings: '"opsz" 144, "SOFT" 0, "wght" 400',
          lineHeight: 1,
        }}
      >
        {value}
      </span>
      <span
        className="eyebrow-tight"
        style={{ color: 'var(--ink-mid)', fontSize: 9.5 }}
      >
        {label}
      </span>
    </div>
  );
}
