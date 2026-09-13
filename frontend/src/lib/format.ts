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
  VERY_HIGH: 'Critical',
};

/**
 * Flood-risk severity tier. Deliberately four levels, matching the backend's real alert
 * scale (LOW/MODERATE/HIGH/VERY_HIGH from `RiskService.calculate_alert`) — not a fifth,
 * invented "very low" bucket the model doesn't produce.
 */
export type RiskTier = 'low' | 'moderate' | 'high' | 'critical';

// Fixed status palette (good/warning/serious/critical): reserved severity meaning, never
// reused for chart series identity, and always paired with a label or icon — on a light
// surface "moderate" and "high" sit under 3:1 contrast by design, so a bare color swatch
// is never the only cue. Same hex values pass 3:1+ against both the light and dark chart
// surface, so no separate dark-mode steps are needed.
const TIER_COLORS: Record<RiskTier, string> = {
  low: '#0ca30c',
  moderate: '#fab219',
  high: '#ec835a',
  critical: '#d03b3b',
};

const TIER_EMOJI: Record<RiskTier, string> = {
  low: '🟢',
  moderate: '🟡',
  high: '🟠',
  critical: '🔴',
};

const TIER_LABELS: Record<RiskTier, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  critical: 'Critical',
};

/** Map the backend's `alert.level` string onto our tier scale. Prefer this over
 *  `classifyRiskTier` whenever the backend has already classified the value — it reflects
 *  the actual configured threshold, which `classifyRiskTier`'s fixed cut points do not. */
export function normalizeAlertLevel(level: string | null | undefined): RiskTier {
  switch (level) {
    case 'MODERATE':
      return 'moderate';
    case 'HIGH':
      return 'high';
    case 'VERY_HIGH':
      return 'critical';
    case 'LOW':
    default:
      return 'low';
  }
}

/**
 * Classify a single 0..1 risk value into a tier using the same cut points the backend
 * documents for its own alert levels (0.4 moderate, 0.7 high, 0.85 critical). Only for
 * values the backend hasn't already classified itself — e.g. individual grid cells, which
 * the `/risk/{id}/grid` endpoint returns as raw numbers with no per-cell alert level.
 */
export function classifyRiskTier(value: number): RiskTier {
  if (value >= 0.85) return 'critical';
  if (value >= 0.7) return 'high';
  if (value >= 0.4) return 'moderate';
  return 'low';
}

export function tierColor(tier: RiskTier): string {
  return TIER_COLORS[tier];
}

export function tierEmoji(tier: RiskTier): string {
  return TIER_EMOJI[tier];
}

export function tierLabel(tier: RiskTier): string {
  return TIER_LABELS[tier];
}
