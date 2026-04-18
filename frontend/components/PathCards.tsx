'use client';
import React from 'react';
import { SectionHeader } from './SectionHeader';

interface Path {
  name: string;
  description: string;
  success_condition: string;
  failure_condition: string;
  recommended: boolean;
}

interface Props {
  data: { path_a: Path; path_b: Path; hybrid: Path };
}

/**
 * Three Opinions — outcome paths rendered as competing positions.
 * The recommended path gets a heavier frame and a "Bench Favored" mark.
 */
export function PathCards({ data }: Props) {
  return (
    <section className="section">
      <SectionHeader
        stage={4}
        description="Three futures projected from the disputed assumptions."
        meta="3 paths · named triggers"
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 0, position: 'relative' }}>
        <Opinion
          ord="I"
          designation="Maximalist"
          path={data.path_a}
          accent="var(--amber)"
          accentInk="var(--amber-ink)"
          accentPaper="var(--amber-paper)"
        />
        <Opinion
          ord="II"
          designation="Conservative"
          path={data.path_b}
          accent="var(--slate)"
          accentInk="var(--slate-ink)"
          accentPaper="var(--slate-paper)"
        />
        <Opinion
          ord="III"
          designation="Hybrid"
          path={data.hybrid}
          accent="var(--forest)"
          accentInk="var(--forest-ink)"
          accentPaper="var(--forest-paper)"
          favored
        />
      </div>
    </section>
  );
}

function Opinion({
  ord,
  designation,
  path,
  accent,
  accentInk,
  accentPaper,
  favored,
}: {
  ord: string;
  designation: string;
  path: Path;
  accent: string;
  accentInk: string;
  accentPaper: string;
  favored?: boolean;
}) {
  return (
    <article
      style={{
        position: 'relative',
        background: favored ? accentPaper : 'var(--paper-bright)',
        border: '0.5px solid var(--ink-rule-strong)',
        borderTop: favored ? `4px solid ${accent}` : `4px solid var(--ink)`,
        padding: '24px 22px 0',
        display: 'flex',
        flexDirection: 'column',
        marginRight: '-0.5px',
        transform: favored ? 'translateY(-6px)' : 'none',
        boxShadow: favored ? `0 4px 0 -2px ${accent}` : 'none',
        zIndex: favored ? 2 : 1,
      }}
    >
      {favored && (
        <div
          style={{
            position: 'absolute',
            top: -14,
            right: 18,
            background: 'var(--ink)',
            color: 'var(--paper-bright)',
            padding: '5px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <span style={{ fontSize: 10 }}>★</span>
          <span className="eyebrow-tight" style={{ color: 'var(--paper-bright)', fontSize: 9 }}>
            Bench Favored
          </span>
        </div>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          marginBottom: 12,
        }}
      >
        <div
          className="display"
          style={{
            fontSize: 38,
            fontStyle: 'italic',
            color: accent,
            lineHeight: 1,
            fontVariationSettings: '"opsz" 144, "SOFT" 100, "wght" 300',
          }}
        >
          {ord}.
        </div>
        <div className="eyebrow-tight" style={{ color: accentInk }}>
          {designation}
        </div>
      </div>

      <h4
        className="display"
        style={{
          margin: '0 0 12px',
          fontSize: 24,
          fontVariationSettings: '"opsz" 144, "SOFT" 20, "wght" 400',
          color: 'var(--ink)',
          letterSpacing: '-0.01em',
        }}
      >
        {path.name}
      </h4>

      <p
        className="serif"
        style={{
          fontSize: 14.5,
          lineHeight: 1.55,
          color: 'var(--ink-mid)',
          margin: '0 0 22px',
          flex: 1,
        }}
      >
        {path.description}
      </p>

      {/* Conditions ledger */}
      <div
        style={{
          marginLeft: -22,
          marginRight: -22,
          padding: '14px 22px 18px',
          borderTop: `1px solid var(--ink)`,
          background: favored ? 'rgba(255,255,255,0.32)' : 'var(--paper-deep)',
        }}
      >
        <Condition
          mark="✓"
          label="Succeeds when"
          text={path.success_condition}
          color="var(--forest-ink)"
          markBg="var(--forest-paper)"
        />
        <div style={{ height: 8 }} />
        <Condition
          mark="✗"
          label="Fails when"
          text={path.failure_condition}
          color="var(--crimson-ink)"
          markBg="var(--crimson-paper)"
        />
      </div>
    </article>
  );
}

function Condition({
  mark,
  label,
  text,
  color,
  markBg,
}: {
  mark: string;
  label: string;
  text: string;
  color: string;
  markBg: string;
}) {
  return (
    <div style={{ display: 'flex', gap: 10 }}>
      <span
        style={{
          width: 18,
          height: 18,
          background: markBg,
          color,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 11,
          fontWeight: 700,
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        {mark}
      </span>
      <div>
        <div
          className="eyebrow-tight"
          style={{ color: 'var(--ink-mid)', marginBottom: 3, fontSize: 9 }}
        >
          {label}
        </div>
        <div
          className="mono"
          style={{ fontSize: 11.5, lineHeight: 1.5, color: 'var(--ink)' }}
        >
          {text}
        </div>
      </div>
    </div>
  );
}
