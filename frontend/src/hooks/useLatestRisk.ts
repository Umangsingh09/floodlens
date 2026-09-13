import { useCallback, useEffect, useState } from 'react';
import { ApiError, fetchLatestRisk, requestRiskRefresh } from '../services/api';
import type { RiskSnapshot } from '../types/risk';

interface RiskState {
  risk: RiskSnapshot | null;
  loading: boolean;
  /** A real backend/network failure — distinct from "no prediction has run yet" (404),
   *  which just leaves `risk` null without setting this. */
  error: boolean;
  refreshError: string | null;
  refreshing: boolean;
  refresh: () => Promise<void>;
}

export function useLatestRisk(): RiskState {
  const [risk, setRisk] = useState<RiskSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchLatestRisk()
      .then((snapshot) => {
        if (!cancelled) {
          setRisk(snapshot);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        // A 404 just means no prediction has run yet — an honest empty state, not a failure.
        const isMissing = err instanceof ApiError && err.status === 404;
        setError(!isMissing);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setRefreshError(null);
    try {
      const snapshot = await requestRiskRefresh();
      setRisk(snapshot);
      setError(false);
    } catch (err) {
      setError(true);
      setRefreshError(err instanceof Error ? err.message : 'Refresh failed');
    } finally {
      setRefreshing(false);
    }
  }, []);

  return { risk, loading, error, refreshError, refreshing, refresh };
}
