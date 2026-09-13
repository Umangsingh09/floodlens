import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api', () => ({
  subscribeToAlerts: vi.fn(),
  unsubscribeFromAlerts: vi.fn(),
}));

import { subscribeToAlerts, unsubscribeFromAlerts } from '../services/api';
import { useAlertSubscription } from './useAlertSubscription';

describe('useAlertSubscription', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('starts with no subscription when localStorage is empty', () => {
    const { result } = renderHook(() => useAlertSubscription());
    expect(result.current.subscriptionId).toBeNull();
  });

  it('picks up a subscription id already stored from a previous visit', () => {
    localStorage.setItem('floodlens.alertSubscriptionId', 'existing-id');
    const { result } = renderHook(() => useAlertSubscription());
    expect(result.current.subscriptionId).toBe('existing-id');
  });

  it('subscribe() stores the real returned id and persists it', async () => {
    vi.mocked(subscribeToAlerts).mockResolvedValue({
      id: 'new-id',
      webhookUrl: 'https://example.com/hook',
      threshold: 0.7,
      createdAt: '2026-01-01T00:00:00Z',
    });

    const { result } = renderHook(() => useAlertSubscription());
    await act(async () => {
      await result.current.subscribe('https://example.com/hook', 0.7);
    });

    expect(result.current.subscriptionId).toBe('new-id');
    expect(localStorage.getItem('floodlens.alertSubscriptionId')).toBe('new-id');
    expect(subscribeToAlerts).toHaveBeenCalledWith('https://example.com/hook', 0.7);
  });

  it('a failed subscribe() surfaces the error and leaves subscriptionId null', async () => {
    vi.mocked(subscribeToAlerts).mockRejectedValue(new Error('invalid webhook'));

    const { result } = renderHook(() => useAlertSubscription());
    await act(async () => {
      await result.current.subscribe('not-a-real-url', 0.7);
    });

    expect(result.current.error).toBe('invalid webhook');
    expect(result.current.subscriptionId).toBeNull();
  });

  it('unsubscribe() clears both state and localStorage even if the request fails', async () => {
    localStorage.setItem('floodlens.alertSubscriptionId', 'existing-id');
    vi.mocked(unsubscribeFromAlerts).mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useAlertSubscription());
    expect(result.current.subscriptionId).toBe('existing-id');

    await act(async () => {
      await result.current.unsubscribe();
    });

    await waitFor(() => expect(result.current.subscriptionId).toBeNull());
    expect(localStorage.getItem('floodlens.alertSubscriptionId')).toBeNull();
  });
});
