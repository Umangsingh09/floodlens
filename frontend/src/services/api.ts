import { API_BASE_URL } from '../lib/constants';
import type { HistoricalEvent } from '../types/events';
import type { RegionInfo } from '../types/region';
import type { RiskGrid, RiskHistoryPoint, RiskSnapshot } from '../types/risk';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`${path} responded with ${response.status}`);
  }
  return response.json() as Promise<T>;
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
