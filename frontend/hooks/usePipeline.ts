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
}

const initial: PipelineState = {
  running: false,
  activeStage: null,
  completedStages: [],
  loadingMessage: '',
  error: null,
  stageData: {},
  finished: false,
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(initial);
  const esRef = useRef<EventSource | null>(null);

  const run = useCallback(() => {
    setState({ ...initial, running: true });

    const es = new EventSource('/api/run');
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
        setState((s) => ({ ...s, running: false, activeStage: null, finished: true }));
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

  return { state, run };
}
