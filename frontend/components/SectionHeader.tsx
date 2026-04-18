'use client';
import React from 'react';

const STAGE_META: Record<number, { act: string; chapter: string; accent: string }> = {
  1: { act: 'Act I',   chapter: 'The Filings',     accent: 'var(--ink)' },
  2: { act: 'Act II',  chapter: 'The Forensics',   accent: 'var(--crimson)' },
  3: { act: 'Act III', chapter: 'The Grounding',   accent: 'var(--slate)' },
  4: { act: 'Act IV',  chapter: 'The Simulation',  accent: 'var(--amber)' },
  5: { act: 'Act V',   chapter: 'The Brief',       accent: 'var(--forest)' },
};

interface Props {
  stage: number;
  description: string;
  meta?: string;
}

/**
 * Editorial chapter mark — mimics a print magazine section opener.
 * "Act II  ·  The Forensics" with a heavy rule and a one-line lede.
 */
export function SectionHeader({ stage, description, meta }: Props) {
  const m = STAGE_META[stage];

  return (
    <header style={{ marginBottom: 14, marginTop: 4 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: 14,
          marginBottom: 8,
        }}
      >
        <span
          className="eyebrow"
          style={{
            color: m.accent,
            letterSpacing: '0.28em',
          }}
        >
          {m.act}
        </span>
        <span style={{ flex: 1, height: 1, background: 'var(--ink)', opacity: 0.85 }} />
        <span className="eyebrow-tight" style={{ color: 'var(--ink-soft)' }}>
          {meta}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}>
        <h3
          className="display"
          style={{
            fontSize: 34,
            fontVariationSettings: '"opsz" 144, "SOFT" 20, "wght" 400',
            margin: 0,
            color: 'var(--ink)',
            letterSpacing: '-0.012em',
          }}
        >
          {m.chapter}
        </h3>
        <span
          className="serif"
          style={{
            fontSize: 16,
            fontStyle: 'italic',
            color: 'var(--ink-mid)',
            lineHeight: 1.3,
            paddingBottom: 5,
          }}
        >
          {description}
        </span>
      </div>
    </header>
  );
}
