'use client';
import React from 'react';
import { SectionHeader } from './SectionHeader';

interface AuditEntry {
  claim: string;
  source_url: string;
  source_name: string;
}

interface Props {
  data: {
    context: string;
    divergence_finding: string;
    recommended_decision: string;
    rationale: string;
    dissenting_opinion: string;
    trigger_conditions: string[];
    audit_log: AuditEntry[];
  };
}

/**
 * The Brief — published as an opinion-page spread.
 * Drop cap on the lede, justified serif body, dissenting column to the side,
 * trigger conditions and citations as marginalia.
 */
export function BriefCard({ data }: Props) {
  return (
    <section className="section">
      <SectionHeader
        stage={5}
        description="The desk's published opinion of record."
        meta="Filed 18 April 2026 · Resolvr Adjudication"
      />

      <article
        style={{
          background: 'var(--paper-bright)',
          border: '0.5px solid var(--ink-rule-strong)',
          padding: '40px 48px 36px',
          position: 'relative',
        }}
      >
        {/* Brief header — newspaper-style */}
        <div
          style={{
            textAlign: 'center',
            paddingBottom: 24,
            borderBottom: '4px double var(--ink)',
            marginBottom: 28,
          }}
        >
          <div
            className="eyebrow"
            style={{ marginBottom: 12, color: 'var(--ink-mid)' }}
          >
            Opinion of the Desk &nbsp;·&nbsp; Case 042 &nbsp;·&nbsp; TechFlow Inc.
          </div>
          <h3
            className="display"
            style={{
              fontSize: 'clamp(36px, 4vw, 52px)',
              margin: '0 0 8px',
              fontVariationSettings: '"opsz" 144, "SOFT" 20, "wght" 400',
              letterSpacing: '-0.015em',
              lineHeight: 1.05,
            }}
          >
            On the question of APAC headcount,
            <br />
            <span
              style={{
                fontStyle: 'italic',
                fontVariationSettings: '"opsz" 144, "SOFT" 100, "wght" 300',
                color: 'var(--crimson)',
              }}
            >
              the desk holds as follows.
            </span>
          </h3>
          <div
            className="serif"
            style={{
              fontSize: 14,
              fontStyle: 'italic',
              color: 'var(--ink-soft)',
              marginTop: 14,
            }}
          >
            Reported by Resolvr Arbitration Desk, on the record.
          </div>
        </div>

        {/* Two-column body */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.6fr 1fr',
            gap: 40,
            alignItems: 'start',
          }}
        >
          {/* LEFT — opinion body */}
          <div>
            <p
              className="serif dropcap"
              style={{
                fontSize: 17,
                lineHeight: 1.65,
                color: 'var(--ink)',
                margin: '0 0 18px',
                textAlign: 'justify',
                hyphens: 'auto',
              }}
            >
              {data.context}
            </p>

            <div
              className="eyebrow-tight"
              style={{ marginTop: 20, marginBottom: 6, color: 'var(--ink-soft)' }}
            >
              On the divergence
            </div>
            <p
              className="serif"
              style={{
                fontSize: 15,
                lineHeight: 1.65,
                color: 'var(--ink-mid)',
                margin: '0 0 24px',
                textAlign: 'justify',
                hyphens: 'auto',
              }}
            >
              {data.divergence_finding}
            </p>

            {/* Holding — the call-out */}
            <div
              style={{
                background: 'var(--ink)',
                color: 'var(--paper-bright)',
                padding: '22px 24px',
                margin: '14px 0 24px',
                position: 'relative',
              }}
            >
              <div
                className="eyebrow-tight"
                style={{ color: 'var(--paper-deep)', opacity: 0.7, marginBottom: 8 }}
              >
                Holding
              </div>
              <p
                className="display"
                style={{
                  margin: 0,
                  fontSize: 22,
                  lineHeight: 1.3,
                  fontVariationSettings: '"opsz" 144, "SOFT" 30, "wght" 400',
                  color: 'var(--paper-bright)',
                  letterSpacing: '-0.01em',
                }}
              >
                {data.recommended_decision}
              </p>
            </div>

            <div
              className="eyebrow-tight"
              style={{ marginBottom: 6, color: 'var(--ink-soft)' }}
            >
              Rationale
            </div>
            <p
              className="serif"
              style={{
                fontSize: 15,
                lineHeight: 1.7,
                color: 'var(--ink)',
                margin: '0 0 28px',
                textAlign: 'justify',
                hyphens: 'auto',
              }}
            >
              {data.rationale}
            </p>

            {/* Dissent — set apart with a vertical rule */}
            <div
              style={{
                borderLeft: `3px solid var(--crimson)`,
                paddingLeft: 18,
                marginTop: 28,
              }}
            >
              <div
                className="eyebrow-tight"
                style={{ color: 'var(--crimson)', marginBottom: 6 }}
              >
                Dissenting Opinion
              </div>
              <p
                className="serif"
                style={{
                  fontSize: 14.5,
                  lineHeight: 1.6,
                  color: 'var(--ink-mid)',
                  margin: 0,
                  fontStyle: 'italic',
                }}
              >
                {data.dissenting_opinion}
              </p>
            </div>
          </div>

          {/* RIGHT — marginalia: triggers and audit */}
          <aside
            style={{
              borderLeft: '0.5px solid var(--ink-rule)',
              paddingLeft: 28,
            }}
          >
            <div className="eyebrow" style={{ marginBottom: 14 }}>
              Trigger Conditions
            </div>
            <div style={{ marginBottom: 32 }}>
              {data.trigger_conditions.map((t, i) => (
                <div
                  key={i}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '34px 1fr',
                    gap: 12,
                    padding: '12px 0',
                    borderBottom: '0.5px solid var(--ink-rule)',
                    borderTop: i === 0 ? '1px solid var(--ink)' : 'none',
                    alignItems: 'baseline',
                  }}
                >
                  <span
                    className="display tabular"
                    style={{
                      fontSize: 26,
                      fontVariationSettings: '"opsz" 144, "SOFT" 0, "wght" 300',
                      color: 'var(--crimson)',
                      lineHeight: 1,
                      fontStyle: 'italic',
                    }}
                  >
                    §{i + 1}
                  </span>
                  <p
                    className="serif"
                    style={{
                      fontSize: 13.5,
                      lineHeight: 1.5,
                      color: 'var(--ink)',
                      margin: 0,
                    }}
                  >
                    {t}
                  </p>
                </div>
              ))}
            </div>

            <div className="eyebrow" style={{ marginBottom: 14 }}>
              Citations of Record
            </div>
            <div>
              {data.audit_log.map((e, i) => (
                <div
                  key={i}
                  style={{
                    padding: '10px 0',
                    borderBottom: '0.5px solid var(--ink-rule)',
                    borderTop: i === 0 ? '1px solid var(--ink)' : 'none',
                  }}
                >
                  <p
                    className="serif"
                    style={{
                      fontSize: 12.5,
                      lineHeight: 1.5,
                      color: 'var(--ink-mid)',
                      margin: '0 0 4px',
                    }}
                  >
                    {e.claim}
                  </p>
                  <a
                    href={e.source_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: 11,
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--slate-ink)',
                      letterSpacing: '0.01em',
                    }}
                  >
                    ↗ {e.source_name}
                  </a>
                </div>
              ))}
            </div>

            {/* Seal */}
            <div
              style={{
                marginTop: 32,
                paddingTop: 18,
                borderTop: '4px double var(--ink)',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <Seal />
              <div>
                <div
                  className="eyebrow-tight"
                  style={{ color: 'var(--ink-mid)', marginBottom: 2 }}
                >
                  So Adjudicated
                </div>
                <div
                  className="serif"
                  style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--ink-mid)' }}
                >
                  Resolvr · Spring Term, 2026
                </div>
              </div>
            </div>
          </aside>
        </div>
      </article>
    </section>
  );
}

function Seal() {
  return (
    <svg width="44" height="44" viewBox="0 0 44 44" aria-hidden>
      <circle cx="22" cy="22" r="20.5" fill="none" stroke="var(--ink)" strokeWidth="0.6" />
      <circle cx="22" cy="22" r="17" fill="none" stroke="var(--ink)" strokeWidth="0.4" />
      <text
        x="22"
        y="20"
        textAnchor="middle"
        fontFamily="Fraunces, serif"
        fontSize="9"
        fontStyle="italic"
        fill="var(--ink)"
      >
        R
      </text>
      <text
        x="22"
        y="30"
        textAnchor="middle"
        fontFamily="IBM Plex Sans, sans-serif"
        fontSize="4"
        letterSpacing="0.16em"
        fill="var(--ink)"
      >
        DESK
      </text>
    </svg>
  );
}
