import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, checkBackendHealth, fetchLatestRisk, resolveAssetUrl } from './api';

describe('ApiError', () => {
  it('carries the real HTTP status so callers can distinguish 404 from a real failure', () => {
    const err = new ApiError('/api/risk/latest responded with 404', 404);
    expect(err.status).toBe(404);
    expect(err.name).toBe('ApiError');
    expect(err).toBeInstanceOf(Error);
  });
});

describe('request (via fetchLatestRisk)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('resolves with the parsed JSON body on a real 200', async () => {
    const body = { predictionId: 'p1', risk: { mean: 0.2 } };
    vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));

    await expect(fetchLatestRisk()).resolves.toEqual(body);
  });

  it('throws an ApiError with status 404 on a real 404 — "no prediction yet", not a crash', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 404 }));

    await expect(fetchLatestRisk()).rejects.toMatchObject({ status: 404 });
  });

  it('throws an ApiError with status 0 when the network request itself fails', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(fetchLatestRisk()).rejects.toMatchObject({ status: 0 });
  });
});

describe('checkBackendHealth', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('is true only for a real successful response', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }));
    await expect(checkBackendHealth()).resolves.toBe(true);
  });

  it('is false on any failure — never throws to the caller', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(checkBackendHealth()).resolves.toBe(false);
  });
});

describe('resolveAssetUrl', () => {
  it('joins the API base with a real relative path', () => {
    expect(resolveAssetUrl('/api/risk/p1/preview.png')).toContain('/api/risk/p1/preview.png');
  });

  it('is null for a null or missing path — no broken <img> src', () => {
    expect(resolveAssetUrl(null)).toBeNull();
    expect(resolveAssetUrl(undefined)).toBeNull();
  });
});
