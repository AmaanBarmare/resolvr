'use client';
import { useCallback, useRef, useState } from 'react';

export type StageNumber = 1 | 2 | 3 | 4 | 5;
export type StageKey = StageNumber | 'done' | 'pipeline' | string;

export interface PipelineState {
  running: boolean;
  activeStage: StageKey | null;
  completedStages: StageNumber[];
  loadingMessage: string;
  error: { stage: StageKey; message: string } | null;
  stageData: Partial<Record<StageNumber, any>>;
  finished: boolean;
  caseId: string | null;
}

const initial: PipelineState = {
  running: false,
  activeStage: null,
  completedStages: [],
  loadingMessage: '',
  error: null,
  stageData: {},
  finished: false,
  caseId: null,
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(initial);
  const esRef = useRef<EventSource | null>(null);

  const run = useCallback((scenarioA?: string, scenarioB?: string) => {
    setState({ ...initial, running: true });

    const params = new URLSearchParams();
    if (scenarioA && scenarioA.trim()) params.set('scenario_a', scenarioA.trim());
    if (scenarioB && scenarioB.trim()) params.set('scenario_b', scenarioB.trim());
    const qs = params.toString();
    const url = qs ? `/api/run?${qs}` : '/api/run';

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (event) => {
      let parsed: any;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        return;
      }

      if (parsed.status === 'loading') {
        setState((s) => ({
          ...s,
          activeStage: parsed.stage,
          loadingMessage: parsed.message || '',
        }));
        return;
      }

      if (parsed.status === 'complete' && parsed.stage !== 'done') {
        setState((s) => ({
          ...s,
          completedStages: [...s.completedStages, parsed.stage as StageNumber],
          stageData: { ...s.stageData, [parsed.stage]: parsed.data },
          activeStage: null,
        }));
        return;
      }

      if (parsed.stage === 'done') {
        setState((s) => ({
          ...s,
          running: false,
          activeStage: null,
          finished: true,
          caseId: parsed.case_id || s.caseId,
        }));
        es.close();
        return;
      }

      if (parsed.status === 'error') {
        setState((s) => ({
          ...s,
          running: false,
          activeStage: null,
          error: { stage: parsed.stage, message: parsed.message || 'Unknown error' },
        }));
        es.close();
        return;
      }
    };

    es.onerror = () => {
      setState((s) => ({
        ...s,
        running: false,
        activeStage: null,
        error: s.error || { stage: 'connection', message: 'Lost connection to backend' },
      }));
      es.close();
    };
  }, []);

  /**
   * Load a previously-saved case by ID — powers shareable /?case={uuid} URLs.
   * Populates stageData immediately (no SSE replay) so visitors see the full
   * arbitration without re-watching the 25s stream.
   */
  const loadCase = useCallback(async (caseId: string) => {
    setState({ ...initial, running: true });
    try {
      const res = await fetch(`/api/case/${encodeURIComponent(caseId)}`);
      const body = await res.json();
      if (!res.ok || body.error) {
        setState({
          ...initial,
          error: {
            stage: 'case',
            message: body.error === 'case_not_found'
              ? `Case ${caseId} not found.`
              : body.error || `Failed to load case ${caseId}.`,
          },
        });
        return;
      }
      const stageMap: Partial<Record<StageNumber, any>> = {};
      const completed: StageNumber[] = [];
      const raw = (body.stage_data || {}) as Record<string, any>;
      for (const key of Object.keys(raw)) {
        const n = Number(key) as StageNumber;
        if (n >= 1 && n <= 5) {
          stageMap[n] = raw[key];
          completed.push(n);
        }
      }
      setState({
        running: false,
        activeStage: null,
        completedStages: completed.sort((a, b) => a - b),
        loadingMessage: '',
        error: null,
        stageData: stageMap,
        finished: true,
        caseId: body.case_id || caseId,
      });
    } catch (e: any) {
      setState({
        ...initial,
        error: { stage: 'case', message: e?.message || 'Failed to load case.' },
      });
    }
  }, []);

  return { state, run, loadCase };
}
