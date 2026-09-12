export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const diffSeconds = Math.max(0, Math.round((Date.now() - then) / 1000));

  if (diffSeconds < 60) return 'moments ago';
  const minutes = Math.floor(diffSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function formatDuration(totalSeconds: number | null | undefined): string {
  if (totalSeconds == null || Number.isNaN(totalSeconds)) return '—';
  const hours = totalSeconds / 3600;
  if (hours < 1) return `${Math.round(totalSeconds / 60)}m`;
  if (hours < 48) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(digits)}%`;
}

interface ParsedScene {
  id: string;
  platform: string;
  date: string;
  time: string;
}

export function parseSceneId(sceneId: string): ParsedScene {
  const match = sceneId.match(/^(S1[A-Z])_.*?_(\d{8})T(\d{6})_/);
  if (!match) {
    return { id: sceneId, platform: '—', date: '—', time: '—' };
  }
  const [, platform, ymd, hms] = match;
  const date = `${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6, 8)}`;
  const time = `${hms.slice(0, 2)}:${hms.slice(2, 4)}`;
  return { id: sceneId, platform, date, time };
}

export function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export const ALERT_LABELS: Record<string, string> = {
  LOW: 'Low',
  MODERATE: 'Moderate',
  HIGH: 'High',
  VERY_HIGH: 'Severe',
};

export type RiskTier = 'safe' | 'moderate' | 'high';

const TIER_COLORS: Record<RiskTier, string> = {
  safe: '#22c55e',
  moderate: '#f59e0b',
  high: '#ef4444',
};

export function classifyRiskTier(value: number): RiskTier {
  if (value >= 0.66) return 'high';
  if (value >= 0.33) return 'moderate';
  return 'safe';
}

export function tierColor(tier: RiskTier): string {
  return TIER_COLORS[tier];
}

export function riskColor(value: number): string {
  const clamped = Math.max(0, Math.min(1, value));
  const stops: Array<[number, [number, number, number]]> = [
    [0, [52, 211, 153]],
    [0.5, [251, 191, 36]],
    [1, [248, 113, 113]],
  ];
  let lower = stops[0];
  let upper = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i += 1) {
    if (clamped >= stops[i][0] && clamped <= stops[i + 1][0]) {
      lower = stops[i];
      upper = stops[i + 1];
      break;
    }
  }
  const span = upper[0] - lower[0] || 1;
  const t = (clamped - lower[0]) / span;
  const rgb = lower[1].map((channel, idx) => Math.round(channel + t * (upper[1][idx] - channel)));
  return `rgb(${rgb.join(', ')})`;
}
