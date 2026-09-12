import { useEffect, useState } from 'react';
import { fetchEvents } from '../services/api';
import type { HistoricalEvent } from '../types/events';

interface EventsState {
  events: HistoricalEvent[];
  loading: boolean;
  error: boolean;
}

export function useEvents(): EventsState {
  const [state, setState] = useState<EventsState>({ events: [], loading: true, error: false });

  useEffect(() => {
    let cancelled = false;
    fetchEvents()
      .then((events) => {
        if (!cancelled) setState({ events, loading: false, error: false });
      })
      .catch(() => {
        if (!cancelled) setState({ events: [], loading: false, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
