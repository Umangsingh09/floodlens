import { useEffect, useState } from 'react';
import { fetchRegion } from '../services/api';
import type { RegionInfo } from '../types/region';

interface RegionState {
  region: RegionInfo | null;
  loading: boolean;
  error: boolean;
}

export function useRegion(): RegionState {
  const [state, setState] = useState<RegionState>({ region: null, loading: true, error: false });

  useEffect(() => {
    let cancelled = false;
    fetchRegion()
      .then((region) => {
        if (!cancelled) setState({ region, loading: false, error: false });
      })
      .catch(() => {
        if (!cancelled) setState({ region: null, loading: false, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
