import { useCallback, useEffect, useState } from 'react';
import { ApiError, fetchLatestRisk, requestRiskRefresh } from '../services/api';
import type { RiskSnapshot } from '../types/risk';

interface RiskState {
  risk: RiskSnapshot | null;
  loading: boolean;
  /** A real backend/network failure message — null for "no prediction has run yet" (404,
   *  an honest empty state) or when there's no error. Set by either the initial fetch or a
   *  failed manual refresh, and cleared on the next success. */
  error: string | null;
  refreshing: boolean;
  refresh: () => Promise<void>;
}

export function useLatestRisk(): RiskState {
  const [risk, setRisk] = useState<RiskSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchLatestRisk()
      .then((snapshot) => {
        if (!cancelled) {
          setRisk(snapshot);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        // A 404 just means no prediction has run yet — an honest empty state, not a failure.
        const isMissing = err instanceof ApiError && err.status === 404;
        setError(isMissing ? null : err instanceof Error ? err.message : 'Failed to load risk data');
        setLoading(false);
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
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    } finally {
      setRefreshing(false);
    }
  }, []);

  return { risk, loading, error, refreshing, refresh };
}
