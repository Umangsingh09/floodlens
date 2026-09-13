import { API_BASE_URL } from '../lib/constants';
import type { AlertSubscription, AlertSubscriptionCount } from '../types/alerts';
import type { HistoricalEvent } from '../types/events';
import type { RegionInfo } from '../types/region';
import type { RiskGrid, RiskHistoryPoint, RiskSnapshot } from '../types/risk';

/** Thrown by `request()` — carries the HTTP status so callers can tell "not found yet"
 *  (404, e.g. no prediction has run) apart from a real backend/network failure. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    // status 0 marks a network-level failure (backend unreachable, CORS, offline).
    throw new ApiError(`${path} could not be reached`, 0);
  }
  if (!response.ok) {
    throw new ApiError(`${path} responded with ${response.status}`, response.status);
  }
  return response.json() as Promise<T>;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    await request('/api/health');
    return true;
  } catch {
    return false;
  }
}

export function fetchRegion(): Promise<RegionInfo> {
  return request<RegionInfo>('/api/region');
}

export function fetchEvents(): Promise<HistoricalEvent[]> {
  return request<HistoricalEvent[]>('/api/events');
}

export function fetchLatestRisk(): Promise<RiskSnapshot> {
  return request<RiskSnapshot>('/api/risk/latest');
}

export function requestRiskRefresh(): Promise<RiskSnapshot> {
  return request<RiskSnapshot>('/api/risk/refresh', { method: 'POST' });
}

export function fetchRiskHistory(limit = 20): Promise<RiskHistoryPoint[]> {
  return request<RiskHistoryPoint[]>(`/api/risk/history?limit=${limit}`);
}

export function fetchRiskGrid(path: string): Promise<RiskGrid> {
  return request<RiskGrid>(path);
}

export function resolveAssetUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return `${API_BASE_URL}${path}`;
}

export function subscribeToAlerts(webhookUrl: string, threshold: number): Promise<AlertSubscription> {
  return request<AlertSubscription>('/api/alerts/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ webhookUrl, threshold }),
  });
}

export async function unsubscribeFromAlerts(subscriptionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${subscriptionId}`, { method: 'DELETE' });
  if (!response.ok && response.status !== 404) {
    throw new ApiError(`/api/alerts/${subscriptionId} responded with ${response.status}`, response.status);
  }
}

export function fetchAlertSubscriptionCount(): Promise<AlertSubscriptionCount> {
  return request<AlertSubscriptionCount>('/api/alerts/count');
}
