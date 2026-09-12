import { useCallback, useEffect, useState } from 'react';
import { fetchLatestRisk, requestRiskRefresh } from '../services/api';
import type { RiskSnapshot } from '../types/risk';

interface RiskState {
  risk: RiskSnapshot | null;
  loading: boolean;
  error: boolean;
  refreshing: boolean;
  refresh: () => Promise<void>;
}

export function useLatestRisk(): RiskState {
  const [risk, setRisk] = useState<RiskSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchLatestRisk()
      .then((snapshot) => {
        if (!cancelled) {
          setRisk(snapshot);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const snapshot = await requestRiskRefresh();
      setRisk(snapshot);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setRefreshing(false);
    }
  }, []);

  return { risk, loading, error, refreshing, refresh };
}
