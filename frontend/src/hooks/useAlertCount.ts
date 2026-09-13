import { useEffect, useState } from 'react';
import { fetchAlertSubscriptionCount } from '../services/api';

/** Real, live count of active alert subscriptions — not a fabricated "N people watching". */
export function useAlertCount(refreshKey?: string | null): number | null {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAlertSubscriptionCount()
      .then((result) => {
        if (!cancelled) setCount(result.count);
      })
      .catch(() => {
        if (!cancelled) setCount(null);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return count;
}
