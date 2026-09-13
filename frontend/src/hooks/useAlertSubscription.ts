import { useCallback, useState } from 'react';
import { subscribeToAlerts, unsubscribeFromAlerts } from '../services/api';

const STORAGE_KEY = 'floodlens.alertSubscriptionId';

function readStoredId(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    // Private browsing / blocked storage — subscribing still works, just won't persist
    // across a reload in this browser.
    return null;
  }
}

interface AlertSubscriptionState {
  subscriptionId: string | null;
  subscribing: boolean;
  error: string | null;
  subscribe: (webhookUrl: string, threshold: number) => Promise<void>;
  unsubscribe: () => Promise<void>;
}

export function useAlertSubscription(): AlertSubscriptionState {
  const [subscriptionId, setSubscriptionId] = useState<string | null>(readStoredId);
  const [subscribing, setSubscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const subscribe = useCallback(async (webhookUrl: string, threshold: number) => {
    setSubscribing(true);
    setError(null);
    try {
      const subscription = await subscribeToAlerts(webhookUrl, threshold);
      setSubscriptionId(subscription.id);
      try {
        localStorage.setItem(STORAGE_KEY, subscription.id);
      } catch {
        // Non-fatal — the subscription is real on the backend either way.
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Subscription failed');
    } finally {
      setSubscribing(false);
    }
  }, []);

  const unsubscribe = useCallback(async () => {
    if (!subscriptionId) return;
    setSubscribing(true);
    try {
      await unsubscribeFromAlerts(subscriptionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unsubscribe failed');
    } finally {
      setSubscriptionId(null);
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {
        // Non-fatal.
      }
      setSubscribing(false);
    }
  }, [subscriptionId]);

  return { subscriptionId, subscribing, error, subscribe, unsubscribe };
}
