import { useState, useEffect, useRef } from 'react';
import { createLeadSSE, createPipelineSSE } from '../api/client';

export function useSSE(leadId) {
  const [state, setState] = useState({ stage: null, status: null, progress: 0, error: null, data: null });
  const esRef = useRef(null);

  useEffect(() => {
    if (!leadId) return;
    const es = createLeadSSE(leadId);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setState({
          stage: data.stage,
          status: data.status,
          progress: _stageToProgress(data.stage),
          error: data.error || null,
          data,
        });
      } catch (_) {}
    };

    es.onerror = () => {
      setState(prev => ({ ...prev, error: 'Connection lost' }));
      es.close();
    };

    return () => es.close();
  }, [leadId]);

  return state;
}

export function usePipelineSSE() {
  const [activePipelines, setActivePipelines] = useState({});
  const esRef = useRef(null);

  useEffect(() => {
    const es = createPipelineSSE();
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const { lead_id, stage, status, name, company } = data;
        setActivePipelines(prev => ({
          ...prev,
          [lead_id]: { lead_id, stage, status, name, company, updated: Date.now() },
        }));
        if (stage === 'complete' || stage === 'failed') {
          setTimeout(() => {
            setActivePipelines(prev => {
              const next = { ...prev };
              delete next[lead_id];
              return next;
            });
          }, 5000);
        }
      } catch (_) {}
    };

    es.onerror = () => es.close();
    return () => es.close();
  }, []);

  return { activePipelines: Object.values(activePipelines) };
}

function _stageToProgress(stage) {
  const map = {
    started: 5, website: 20, linkedin: 40, news: 60, scoring: 75, drafts: 90, complete: 100,
  };
  return map[stage] || 0;
}
