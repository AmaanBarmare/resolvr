'use client';
import React from 'react';
import { SectionHeader } from './SectionHeader';

interface Assumption {
  variable: string;
  value: string;
  source: string;
}

interface Agent {
  recommendation: string;
  assumptions: Assumption[];
  source: string;
}

interface Props {
  data: { agent_a: Agent; agent_b: Agent };
}

/**
 * The Filings — two agent recommendations rendered as opposing court briefs.
 * They face each other with a center "vs" rule. Sharp typographic contrast.
 */
export function AgentCards({ data }: Props) {
  return (
    <section className="section">
      <SectionHeader
        stage={1}
        description="The two agents file their counsel before the desk."
        meta={`Source: ${data.agent_a.source} · ${data.agent_b.source}`}
      />

      <div
        style={{
          background: 'var(--paper-bright)',
          border: '0.5px solid var(--ink-rule-strong)',
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          position: 'relative',
        }}
      >
        <Filing
          side="petitioner"
          designation="Agent A"
          house="Revenue Counsel"
          accent="var(--amber)"
          accentInk="var(--amber-ink)"
          accentPaper="var(--amber-paper)"
          agent={data.agent_a}
        />

        {/* Center rule with VS marker */}
        <div
          style={{
            width: 1,
            background: 'var(--ink)',
            opacity: 0.85,
            position: 'relative',
            margin: '0',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'var(--paper-bright)',
              padding: '12px 8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <span
              className="display"
              style={{
                fontSize: 22,
                fontStyle: 'italic',
                fontVariationSettings: '"opsz" 144, "SOFT" 100, "wght" 300',
                color: 'var(--ink)',
                lineHeight: 1,
              }}
            >
              vs.
            </span>
            <span
              className="eyebrow-tight"
              style={{ fontSize: 8, color: 'var(--ink-soft)', writingMode: 'horizontal-tb' }}
            >
              In re
            </span>
          </div>
        </div>

        <Filing
          side="respondent"
          designation="Agent B"
          house="Risk Counsel"
          accent="var(--slate)"
          accentInk="var(--slate-ink)"
          accentPaper="var(--slate-paper)"
          agent={data.agent_b}
        />
      </div>
    </section>
  );
}

function Filing({
  side,
  designation,
  house,
  accent,
  accentInk,
  accentPaper,
  agent,
}: {
  side: 'petitioner' | 'respondent';
  designation: string;
  house: string;
  accent: string;
  accentInk: string;
  accentPaper: string;
  agent: Agent;
}) {
  const isLeft = side === 'petitioner';

  return (
    <article style={{ padding: '24px 28px 22px' }}>
      {/* Filing header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: 18,
          paddingBottom: 10,
          borderBottom: `0.5px solid ${accent}`,
        }}
      >
        <div>
          <div
            className="eyebrow-tight"
            style={{ color: accentInk, marginBottom: 4 }}
          >
            {isLeft ? 'Petitioner' : 'Respondent'}
          </div>
          <div
            className="display"
            style={{
              fontSize: 26,
              fontVariationSettings: '"opsz" 144, "SOFT" 30, "wght" 400',
              color: 'var(--ink)',
              lineHeight: 1.05,
            }}
          >
            {house}
          </div>
        </div>
        <div
          className="mono"
          style={{ fontSize: 11, color: 'var(--ink-soft)', letterSpacing: '0.02em' }}
        >
          {designation}
        </div>
      </div>

      {/* The recommendation — set as a pull quote */}
      <div style={{ marginBottom: 22, position: 'relative', paddingLeft: 18 }}>
        <span
          className="display"
          style={{
            position: 'absolute',
            left: -2,
            top: -10,
            fontSize: 48,
            fontStyle: 'italic',
            color: accent,
            lineHeight: 1,
            opacity: 0.7,
            fontVariationSettings: '"opsz" 144, "SOFT" 100, "wght" 300',
          }}
          aria-hidden
        >
          &ldquo;
        </span>
        <p
          className="serif"
          style={{
            fontSize: 18,
            lineHeight: 1.42,
            color: 'var(--ink)',
            fontStyle: 'italic',
            margin: 0,
            letterSpacing: '-0.005em',
          }}
        >
          {agent.recommendation}
        </p>
      </div>

      {/* Assumptions ledger */}
      <div>
        <div
          className="eyebrow-tight"
          style={{ marginBottom: 8, color: 'var(--ink-soft)' }}
        >
          Stipulated Facts
        </div>
        <div style={{ borderTop: '1px solid var(--ink)' }}>
          {agent.assumptions.map((a, i) => (
            <div
              key={a.variable}
              style={{
                display: 'grid',
                gridTemplateColumns: '20px 1fr auto',
                gap: 12,
                padding: '8px 0',
                borderBottom: '0.5px solid var(--ink-rule)',
                alignItems: 'baseline',
              }}
            >
              <span className="marker tabular">
                {String(i + 1).padStart(2, '0')}
              </span>
              <div>
                <div className="mono" style={{ fontSize: 11.5, color: 'var(--ink)' }}>
                  {a.variable}
                </div>
                <div className="mono" style={{ fontSize: 9.5, color: 'var(--ink-soft)', marginTop: 2 }}>
                  {a.source}
                </div>
              </div>
              <span
                className="mono tabular"
                style={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: accentInk,
                  background: accentPaper,
                  padding: '2px 8px',
                }}
              >
                {a.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
