import { useEffect, useState } from 'react';
import { fetchRiskGrid } from '../services/api';
import type { RiskGrid } from '../types/risk';

export function useRiskGrid(gridUrl: string | null | undefined): RiskGrid | null {
  const [grid, setGrid] = useState<RiskGrid | null>(null);

  useEffect(() => {
    if (!gridUrl) return;
    let cancelled = false;
    fetchRiskGrid(gridUrl).then((data) => {
      if (!cancelled) setGrid(data);
    });
    return () => {
      cancelled = true;
    };
  }, [gridUrl]);

  return grid;
}
