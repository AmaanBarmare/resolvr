'use client';
import React from 'react';

interface GroundedRow {
  verdict: 'outlier' | 'aligned' | 'unverifiable';
}

interface Props {
  loading: boolean;
  loadingMessage?: string;
  grounded?: GroundedRow[];
}

/**
 * Verification ribbon — sits inline as a thin banner, not a card.
 * Either a live "wires running" indicator or a one-line tally.
 */
export function GroundingStatus({ loading, loadingMessage, grounded }: Props) {
  if (loading) {
    return (
      <div
        className="section"
        style={{
          background: 'var(--paper-deep)',
          border: '0.5px solid var(--ink-rule-strong)',
          borderLeft: '3px solid var(--slate)',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
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
          {loadingMessage || 'Querying You.com for enterprise SaaS benchmarks…'}
        </span>
      </div>
    );
  }

  if (!grounded) return null;

  const outliers = grounded.filter((g) => g.verdict === 'outlier').length;
  const aligned = grounded.filter((g) => g.verdict === 'aligned').length;
  const unver = grounded.filter((g) => g.verdict === 'unverifiable').length;

  return (
    <div
      className="section"
      style={{
        background: 'var(--paper-bright)',
        border: '0.5px solid var(--ink-rule-strong)',
        borderLeft: '3px solid var(--forest)',
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
      }}
    >
      <span className="eyebrow-tight" style={{ color: 'var(--forest-ink)' }}>
        Grounding Returned
      </span>
      <span style={{ height: 18, width: 1, background: 'var(--ink-rule-strong)' }} />
      <Tally label="Verified" value={grounded.length} accent="var(--ink)" />
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
  );
}

function Tally({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
      <span
        className="display tabular"
        style={{ fontSize: 22, color: accent, fontVariationSettings: '"opsz" 144, "SOFT" 0, "wght" 400', lineHeight: 1 }}
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
