'use client';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { usePipeline } from '../hooks/usePipeline';
import { TopBar } from '../components/TopBar';
import { Docket } from '../components/Docket';
import { PipelineBar } from '../components/PipelineBar';
import { AgentCards } from '../components/AgentCards';
import { DivergenceTable } from '../components/DivergenceTable';
import { GroundingStatus } from '../components/GroundingStatus';
import { PathCards } from '../components/PathCards';
import { BriefCard } from '../components/BriefCard';
import { ActNav } from '../components/ActNav';

export default function Page() {
  const { state, run } = usePipeline();
  const { stageData, activeStage, completedStages, loadingMessage, finished, error, running } = state;

  const groundedByVar = useMemo(() => {
    const g = stageData[3] as { grounded_assumptions?: any[] } | undefined;
    if (!g?.grounded_assumptions) return {};
    return Object.fromEntries(g.grounded_assumptions.map((r: any) => [r.variable, r]));
  }, [stageData]);

  const hasResults = Boolean(stageData[1]);

  // Page-by-page navigation across acts. Auto-advance to whichever act is the
  // most recently completed — but only once per stage, so the user can click
  // Prev to revisit earlier acts without being yanked back.
  const [currentAct, setCurrentAct] = useState<number | null>(null);
  const maxAutoJumpedRef = useRef(0);

  useEffect(() => {
    // Reset on new run
    if (running && !stageData[1]) {
      setCurrentAct(null);
      maxAutoJumpedRef.current = 0;
    }
  }, [running, stageData]);

  useEffect(() => {
    const completed = Object.keys(stageData)
      .map(Number)
      .filter((n) => n >= 1 && n <= 5);
    if (completed.length === 0) return;
    const latest = Math.max(...completed);
    if (latest > maxAutoJumpedRef.current) {
      setCurrentAct(latest);
      maxAutoJumpedRef.current = latest;
    }
  }, [stageData]);

  const availableActs: number[] = Object.keys(stageData)
    .map(Number)
    .filter((n) => n >= 1 && n <= 5);

  const renderAct = (act: number) => {
    switch (act) {
      case 1:
        return stageData[1] ? <AgentCards data={stageData[1] as any} /> : null;
      case 2:
        return stageData[2] ? (
          <DivergenceTable data={stageData[2] as any} grounded={groundedByVar as any} />
        ) : null;
      case 3:
        return (
          <GroundingStatus
            loading={activeStage === 3 && !stageData[3]}
            loadingMessage={loadingMessage}
            grounded={stageData[3]?.grounded_assumptions}
          />
        );
      case 4:
        return stageData[4] ? <PathCards data={stageData[4] as any} /> : null;
      case 5:
        return stageData[5] ? <BriefCard data={stageData[5] as any} /> : null;
      default:
        return null;
    }
  };

  const loadingStageNum =
    typeof activeStage === 'number' ? activeStage : null;

  return (
    <main className="page">
      <TopBar running={state.running} finished={finished} onRun={run} />

      <Docket
        running={state.running}
        finished={finished}
        hasResults={hasResults}
        onRun={run}
      />

      <PipelineBar activeStage={activeStage} completedStages={completedStages} />

      {error && (
        <div
          className="section"
          style={{
            background: 'var(--crimson-paper)',
            color: 'var(--crimson-ink)',
            border: '0.5px solid var(--crimson)',
            borderLeft: '3px solid var(--crimson)',
            padding: '14px 18px',
          }}
        >
          <div className="eyebrow-tight" style={{ color: 'var(--crimson)', marginBottom: 4 }}>
            Stage {String(error.stage)} · Mistrial
          </div>
          <div className="serif" style={{ fontSize: 14, fontStyle: 'italic' }}>
            {error.message}
          </div>
        </div>
      )}

      {currentAct !== null && (
        <>
          {renderAct(currentAct)}
          <ActNav
            currentAct={currentAct}
            availableActs={availableActs}
            loadingStage={loadingStageNum}
            onSelect={setCurrentAct}
          />
        </>
      )}

      {/* Footer colophon */}
      <footer
        style={{
          marginTop: 24,
          paddingTop: 18,
          borderTop: '0.5px solid var(--ink-rule)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
        }}
      >
        <span
          className="eyebrow-tight"
          style={{ color: 'var(--ink-soft)' }}
        >
          Resolvr — The Arbitration Desk
        </span>
        <span
          className="serif"
          style={{
            fontStyle: 'italic',
            fontSize: 12,
            color: 'var(--ink-soft)',
          }}
        >
          Set in Fraunces, Newsreader, &amp; IBM Plex. Printed on virtual paper, 2026.
        </span>
      </footer>
    </main>
  );
}
