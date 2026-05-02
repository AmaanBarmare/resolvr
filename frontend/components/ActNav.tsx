'use client';
import React from 'react';

const ACT_META: Record<number, { roman: string; name: string; accent: string }> = {
  1: { roman: 'I',   name: 'The Filings',     accent: 'var(--ink)' },
  2: { roman: 'II',  name: 'The Forensics',   accent: 'var(--crimson)' },
  3: { roman: 'III', name: 'The Grounding',   accent: 'var(--slate)' },
  4: { roman: 'IV',  name: 'The Simulation',  accent: 'var(--amber)' },
  5: { roman: 'V',   name: 'The Brief',       accent: 'var(--forest)' },
};

interface Props {
  currentAct: number;          // 1-5
  availableActs: number[];     // which acts have data ready
  loadingStage: number | null; // which stage is currently streaming, if any
  onSelect: (act: number) => void;
}

/**
 * Per-page navigation between acts. Prev disabled at I, Next disabled until
 * the next act has actually streamed in (shows "Awaiting Act N…" instead).
 */
export function ActNav({ currentAct, availableActs, loadingStage, onSelect }: Props) {
  const prevAct = currentAct - 1;
  const nextAct = currentAct + 1;
  const prevAvailable = prevAct >= 1;
  const nextAvailable = nextAct <= 5 && availableActs.includes(nextAct);
  const nextLoading = nextAct <= 5 && loadingStage === nextAct;

  return (
    <nav
      style={{
        marginTop: 14,
        background: 'var(--paper-bright)',
        border: '0.5px solid var(--ink-rule-strong)',
        padding: '14px 20px',
        display: 'grid',
        gridTemplateColumns: '1fr auto 1fr',
        gap: 18,
        alignItems: 'center',
      }}
    >
      {/* Prev */}
      <div style={{ justifySelf: 'start' }}>
        {prevAvailable ? (
          <NavButton
            direction="prev"
            roman={ACT_META[prevAct].roman}
            name={ACT_META[prevAct].name}
            accent={ACT_META[prevAct].accent}
            onClick={() => onSelect(prevAct)}
          />
        ) : (
          <span
            className="eyebrow-tight"
            style={{ color: 'var(--ink-faint)' }}
          >
            ◇ First in proceeding
          </span>
        )}
      </div>

      {/* Center — counter */}
      <div
        className="eyebrow-tight"
        style={{
          color: 'var(--ink-mid)',
          letterSpacing: '0.22em',
          textAlign: 'center',
        }}
      >
        Act {ACT_META[currentAct].roman} of V
      </div>

      {/* Next */}
      <div style={{ justifySelf: 'end' }}>
        {currentAct === 5 ? (
          <span
            className="eyebrow-tight"
            style={{ color: 'var(--ink-faint)' }}
          >
            Adjudication concluded ◇
          </span>
        ) : nextAvailable ? (
          <NavButton
            direction="next"
            roman={ACT_META[nextAct].roman}
            name={ACT_META[nextAct].name}
            accent={ACT_META[nextAct].accent}
            onClick={() => onSelect(nextAct)}
          />
        ) : (
          <PendingNext
            roman={ACT_META[nextAct].roman}
            name={ACT_META[nextAct].name}
            loading={nextLoading}
          />
        )}
      </div>
    </nav>
  );
}

function NavButton({
  direction,
  roman,
  name,
  accent,
  onClick,
}: {
  direction: 'prev' | 'next';
  roman: string;
  name: string;
  accent: string;
  onClick: () => void;
}) {
  const arrow = direction === 'prev' ? '←' : '→';
  return (
    <button
      onClick={onClick}
      style={{
        background: 'transparent',
        border: 'none',
        padding: '6px 4px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'baseline',
        gap: 10,
        textAlign: direction === 'prev' ? 'left' : 'right',
        flexDirection: direction === 'prev' ? 'row' : 'row-reverse',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.7')}
      onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
    >
      <span
        className="display"
        style={{
          fontSize: 24,
          color: accent,
          fontVariationSettings: '"opsz" 144, "SOFT" 0, "wght" 400',
          lineHeight: 1,
        }}
      >
        {arrow}
      </span>
      <span style={{ display: 'flex', flexDirection: 'column' }}>
        <span
          className="eyebrow-tight"
          style={{ color: 'var(--ink-mid)', fontSize: 9 }}
        >
          {direction === 'prev' ? 'Previous' : 'Next'} · Act {roman}
        </span>
        <span
          className="serif"
          style={{ fontSize: 14, fontStyle: 'italic', color: accent, marginTop: 1 }}
        >
          {name}
        </span>
      </span>
    </button>
  );
}

function PendingNext({
  roman,
  name,
  loading,
}: {
  roman: string;
  name: string;
  loading: boolean;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        opacity: 0.65,
      }}
    >
      <span style={{ display: 'flex', flexDirection: 'column', textAlign: 'right' }}>
        <span
          className="eyebrow-tight"
          style={{ color: 'var(--ink-faint)', fontSize: 9 }}
        >
          {loading ? 'On the wires' : 'Awaiting'} · Act {roman}
        </span>
        <span
          className="serif"
          style={{ fontSize: 14, fontStyle: 'italic', color: 'var(--ink-faint)', marginTop: 1 }}
        >
          {name}
        </span>
      </span>
      {loading ? (
        <span className="spin" style={{ color: 'var(--ink-soft)' }} />
      ) : (
        <span
          className="display"
          style={{
            fontSize: 24,
            color: 'var(--ink-faint)',
            fontVariationSettings: '"opsz" 144, "SOFT" 0, "wght" 400',
            lineHeight: 1,
          }}
        >
          ◇
        </span>
      )}
    </div>
  );
}
