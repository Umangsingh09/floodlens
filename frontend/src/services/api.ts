import { API_BASE_URL } from '../lib/constants';
import type { HealthStatus } from '../types/health';

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json() as Promise<HealthStatus>;
}
