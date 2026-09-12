import { useEffect, useState } from 'react';
import { fetchRiskHistory } from '../services/api';
import type { RiskHistoryPoint } from '../types/risk';

export function useRiskHistory(refreshKey?: string): RiskHistoryPoint[] {
  const [points, setPoints] = useState<RiskHistoryPoint[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchRiskHistory().then((data) => {
      if (!cancelled) setPoints(data);
    });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return points;
}
