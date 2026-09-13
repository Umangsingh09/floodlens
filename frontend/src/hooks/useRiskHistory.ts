import { useEffect, useState } from 'react';
import { fetchRiskHistory } from '../services/api';
import type { RiskHistoryPoint } from '../types/risk';

interface RiskHistoryState {
  points: RiskHistoryPoint[];
  loading: boolean;
}

export function useRiskHistory(refreshKey?: string, limit = 20): RiskHistoryState {
  const [state, setState] = useState<RiskHistoryState>({ points: [], loading: true });

  useEffect(() => {
    let cancelled = false;
    // Deliberately doesn't flip `loading` back to true on refetch (e.g. after a manual
    // refresh) — keep showing the last known points rather than flashing a skeleton.
    fetchRiskHistory(limit)
      .then((points) => {
        if (!cancelled) setState({ points, loading: false });
      })
      .catch(() => {
        if (!cancelled) setState({ points: [], loading: false });
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey, limit]);

  return state;
}
