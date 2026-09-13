import { useEffect, useState } from 'react';
import { checkBackendHealth } from '../services/api';

export type BackendStatus = 'checking' | 'online' | 'offline';

const POLL_INTERVAL_MS = 30_000;

/** Polls the real `/api/health` endpoint — never a fabricated/simulated status. */
export function useBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>('checking');

  useEffect(() => {
    let cancelled = false;

    const check = () => {
      checkBackendHealth().then((healthy) => {
        if (!cancelled) setStatus(healthy ? 'online' : 'offline');
      });
    };

    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return status;
}
