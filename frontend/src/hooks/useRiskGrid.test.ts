import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<typeof import('../services/api')>('../services/api');
  return { ...actual, fetchRiskGrid: vi.fn() };
});

import { fetchRiskGrid } from '../services/api';
import type { RiskGrid } from '../types/risk';
import { useRiskGrid } from './useRiskGrid';

const GRID = (n: number): RiskGrid => ({ rows: 1, cols: 1, cells: [{ lat: 0, lon: 0, value: n }] });

describe('useRiskGrid', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns null grid and no loading when there is no gridUrl yet', () => {
    const { result } = renderHook(() => useRiskGrid(null));
    expect(result.current).toEqual({ grid: null, loading: false });
  });

  it('loads the real grid for a given url and reports loading while in flight', async () => {
    let resolveFetch!: (v: RiskGrid) => void;
    vi.mocked(fetchRiskGrid).mockReturnValue(new Promise((r) => (resolveFetch = r)));

    const { result } = renderHook(() => useRiskGrid('/api/risk/p-unique-1/grid'));
    expect(result.current.loading).toBe(true);
    expect(result.current.grid).toBeNull();

    resolveFetch(GRID(1));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.grid).toEqual(GRID(1));
  });

  it('dedupes two simultaneous callers for the same url into one real network request', async () => {
    vi.mocked(fetchRiskGrid).mockResolvedValue(GRID(2));

    const a = renderHook(() => useRiskGrid('/api/risk/p-unique-2/grid'));
    const b = renderHook(() => useRiskGrid('/api/risk/p-unique-2/grid'));

    await waitFor(() => expect(a.result.current.loading).toBe(false));
    await waitFor(() => expect(b.result.current.loading).toBe(false));

    expect(fetchRiskGrid).toHaveBeenCalledTimes(1);
    expect(a.result.current.grid).toEqual(GRID(2));
    expect(b.result.current.grid).toEqual(GRID(2));
  });

  it('reuses the cached result for a url already fetched, without a second request', async () => {
    vi.mocked(fetchRiskGrid).mockResolvedValue(GRID(3));

    const first = renderHook(() => useRiskGrid('/api/risk/p-unique-3/grid'));
    await waitFor(() => expect(first.result.current.loading).toBe(false));

    const second = renderHook(() => useRiskGrid('/api/risk/p-unique-3/grid'));
    // A cache hit still resolves via a microtask inside the effect (not synchronously on
    // mount), but never calls fetchRiskGrid again.
    await waitFor(() => expect(second.result.current.loading).toBe(false));
    expect(second.result.current.grid).toEqual(GRID(3));
    expect(fetchRiskGrid).toHaveBeenCalledTimes(1);
  });

  it('resets to loading (not the stale grid) when the url changes to a new prediction', async () => {
    vi.mocked(fetchRiskGrid).mockResolvedValueOnce(GRID(4)).mockResolvedValueOnce(GRID(5));

    const { result, rerender } = renderHook(({ url }) => useRiskGrid(url), {
      initialProps: { url: '/api/risk/p-unique-4/grid' },
    });
    await waitFor(() => expect(result.current.grid).toEqual(GRID(4)));

    rerender({ url: '/api/risk/p-unique-5/grid' });
    // Never shows prediction 4's grid as if it belonged to prediction 5.
    expect(result.current.grid).toBeNull();
    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.grid).toEqual(GRID(5)));
  });
});
