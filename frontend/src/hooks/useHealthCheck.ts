import { useEffect, useState } from 'react';
import { fetchHealth } from '../services/api';

export type BackendConnectionState = 'checking' | 'online' | 'offline';

export function useHealthCheck(): BackendConnectionState {
  const [state, setState] = useState<BackendConnectionState>('checking');

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then(() => {
        if (!cancelled) setState('online');
      })
      .catch(() => {
        if (!cancelled) setState('offline');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
