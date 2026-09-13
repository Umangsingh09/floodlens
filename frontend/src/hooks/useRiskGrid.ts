import { useEffect, useState } from 'react';
import { fetchRiskGrid } from '../services/api';
import type { RiskGrid } from '../types/risk';

// The dashboard's summary cards and the risk map both need the same grid for the same
// prediction at the same time — this dedupes that into one real network request instead of
// two, and lets whichever mounts second reuse the first's in-flight fetch or cached result.
const gridCache = new Map<string, RiskGrid>();
const inFlight = new Map<string, Promise<RiskGrid>>();

function loadGrid(gridUrl: string): Promise<RiskGrid> {
  const cached = gridCache.get(gridUrl);
  if (cached) return Promise.resolve(cached);

  const pending = inFlight.get(gridUrl);
  if (pending) return pending;

  const request = fetchRiskGrid(gridUrl)
    .then((data) => {
      gridCache.set(gridUrl, data);
      return data;
    })
    .finally(() => {
      inFlight.delete(gridUrl);
    });
  inFlight.set(gridUrl, request);
  return request;
}

interface RiskGridState {
  grid: RiskGrid | null;
  loading: boolean;
}

export function useRiskGrid(gridUrl: string | null | undefined): RiskGridState {
  const [state, setState] = useState<RiskGridState>({ grid: null, loading: Boolean(gridUrl) });
  // Tracks the gridUrl the current `state` was computed for, so a change can be detected and
  // reset during render — never show a stale grid from a previous prediction as if current.
  const [stateFor, setStateFor] = useState(gridUrl);

  if (gridUrl !== stateFor) {
    setStateFor(gridUrl);
    setState({ grid: null, loading: Boolean(gridUrl) });
  }

  useEffect(() => {
    if (!gridUrl) return;
    let cancelled = false;
    loadGrid(gridUrl)
      .then((data) => {
        if (!cancelled) setState({ grid: data, loading: false });
      })
      .catch(() => {
        if (!cancelled) setState({ grid: null, loading: false });
      });
    return () => {
      cancelled = true;
    };
  }, [gridUrl]);

  return state;
}
