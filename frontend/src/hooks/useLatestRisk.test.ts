import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../services/api';
import { useLatestRisk } from './useLatestRisk';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<typeof import('../services/api')>('../services/api');
  return { ...actual, fetchLatestRisk: vi.fn(), requestRiskRefresh: vi.fn() };
});

import { fetchLatestRisk, requestRiskRefresh } from '../services/api';

const RISK = { predictionId: 'p1', risk: { mean: 0.2 } } as never;

describe('useLatestRisk', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('loads real data on mount and clears the loading flag', async () => {
    vi.mocked(fetchLatestRisk).mockResolvedValue(RISK);

    const { result } = renderHook(() => useLatestRisk());
    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.risk).toEqual(RISK);
    expect(result.current.error).toBeNull();
  });

  it('treats a 404 as "no prediction yet" — not an error the UI should alarm on', async () => {
    vi.mocked(fetchLatestRisk).mockRejectedValue(new ApiError('not found', 404));

    const { result } = renderHook(() => useLatestRisk());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.risk).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('surfaces a real backend/network failure as a visible error message', async () => {
    vi.mocked(fetchLatestRisk).mockRejectedValue(new ApiError('boom', 500));

    const { result } = renderHook(() => useLatestRisk());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('boom');
  });

  it('refresh() replaces the risk snapshot and clears any prior error on success', async () => {
    vi.mocked(fetchLatestRisk).mockRejectedValue(new ApiError('boom', 500));
    vi.mocked(requestRiskRefresh).mockResolvedValue(RISK);

    const { result } = renderHook(() => useLatestRisk());
    await waitFor(() => expect(result.current.error).toBe('boom'));

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.risk).toEqual(RISK);
    expect(result.current.error).toBeNull();
    expect(result.current.refreshing).toBe(false);
  });

  it('a failed refresh sets a visible error and always clears the refreshing flag', async () => {
    vi.mocked(fetchLatestRisk).mockResolvedValue(RISK);
    vi.mocked(requestRiskRefresh).mockRejectedValue(new Error('refresh exploded'));

    const { result } = renderHook(() => useLatestRisk());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.error).toBe('refresh exploded');
    expect(result.current.refreshing).toBe(false);
  });
});
