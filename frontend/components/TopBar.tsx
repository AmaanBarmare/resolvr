'use client';
import React from 'react';

interface Props {
  running: boolean;
  finished: boolean;
  onRun: () => void;
}

/**
 * Masthead — the editorial nameplate that anchors the page.
 * Mirrors a real newspaper plate: meta strip, plate, double rule.
 */
export function TopBar({ running, finished }: Props) {
  return (
    <header style={{ position: 'relative' }}>
      {/* META STRIP — issue, edition, date */}
      <div
        className="eyebrow-tight"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          paddingBottom: 10,
          borderBottom: '0.5px solid var(--ink-rule)',
        }}
      >
        <span>Vol. I&nbsp;&middot;&nbsp;No. 042&nbsp;&middot;&nbsp;Spring Edition</span>
        <span style={{ display: 'flex', gap: 18 }}>
          <span>Friday, 18 April 2026</span>
          <span style={{ color: finished ? 'var(--forest-ink)' : running ? 'var(--amber-ink)' : 'var(--ink-soft)' }}>
            {finished ? '● Verdict on file' : running ? '● In session' : '● Desk open'}
          </span>
        </span>
      </div>

      {/* PLATE */}
      <div
        style={{
          paddingTop: 22,
          paddingBottom: 16,
          display: 'grid',
          gridTemplateColumns: 'auto 1fr auto',
          alignItems: 'end',
          gap: 32,
        }}
      >
        {/* Crest — geometric mark */}
        <Crest />

        {/* Logotype — center */}
        <div style={{ textAlign: 'center', paddingBottom: 6 }}>
          <h1
            className="display"
            style={{
              fontVariationSettings: '"opsz" 144, "SOFT" 30, "wght" 400',
              fontSize: 'clamp(56px, 8vw, 104px)',
              margin: 0,
              letterSpacing: '0.06em',
            }}
          >
            R<span style={{ fontStyle: 'italic', fontVariationSettings: '"opsz" 144, "SOFT" 100, "wght" 300' }}>e</span>solvr
          </h1>
          <div
            className="eyebrow"
            style={{
              marginTop: 6,
              fontSize: 11,
              letterSpacing: '0.42em',
              color: 'var(--ink-mid)',
            }}
          >
            The&nbsp;&nbsp;Arbitration&nbsp;&nbsp;Desk
          </div>
        </div>

        {/* Right meta — disposition status */}
        <div style={{ textAlign: 'right', paddingBottom: 6, minWidth: 150 }}>
          <div className="eyebrow-tight" style={{ marginBottom: 4 }}>Docket</div>
          <div className="mono" style={{ fontSize: 13, fontWeight: 500, letterSpacing: '0.02em' }}>
            042 — TFLO
          </div>
          <div className="eyebrow-tight" style={{ marginTop: 6, color: 'var(--ink-soft)' }}>
            Adjudicated by Resolvr
          </div>
        </div>
      </div>

      {/* DOUBLE RULE — newspaper plate base */}
      <div style={{ borderTop: '1px solid var(--ink)', height: 4, borderBottom: '1px solid var(--ink)' }} />

      {/* SUB-MASTHEAD — section labels like a newspaper section bar */}
      <div
        className="eyebrow"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 0 0',
          fontSize: 10,
          color: 'var(--ink-mid)',
        }}
      >
        <span>Filings · Forensics · Grounding · Simulation · Brief</span>
        <span style={{ fontStyle: 'italic', fontFamily: 'var(--font-serif)', textTransform: 'none', letterSpacing: 0, fontSize: 12, color: 'var(--ink-mid)' }}>
          &ldquo;When agents disagree, someone decides.&rdquo;
        </span>
      </div>
    </header>
  );
}

function Crest() {
  return (
    <svg width="62" height="62" viewBox="0 0 62 62" aria-hidden style={{ marginBottom: 4 }}>
      {/* Outer ring */}
      <circle cx="31" cy="31" r="29.5" fill="none" stroke="var(--ink)" strokeWidth="0.6" />
      <circle cx="31" cy="31" r="26" fill="none" stroke="var(--ink)" strokeWidth="0.4" />
      {/* Scales of justice — abstract */}
      <line x1="31" y1="14" x2="31" y2="48" stroke="var(--ink)" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="14" y1="22" x2="48" y2="22" stroke="var(--ink)" strokeWidth="0.8" strokeLinecap="round" />
      {/* Left pan */}
      <path d="M14 22 L10 32 A6 6 0 0 0 18 32 Z" fill="none" stroke="var(--crimson)" strokeWidth="0.9" />
      {/* Right pan */}
      <path d="M48 22 L44 32 A6 6 0 0 0 52 32 Z" fill="none" stroke="var(--slate)" strokeWidth="0.9" />
      {/* Base */}
      <line x1="22" y1="48" x2="40" y2="48" stroke="var(--ink)" strokeWidth="1.4" strokeLinecap="round" />
      {/* Top finial */}
      <circle cx="31" cy="14" r="1.6" fill="var(--ink)" />
    </svg>
  );
}
