import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  classifyRiskTier,
  computeTargetTimestamp,
  formatDuration,
  formatPercent,
  formatRelativeTime,
  normalizeAlertLevel,
  parseSceneId,
  tierColor,
  tierEmoji,
  tierLabel,
} from './format';

describe('classifyRiskTier', () => {
  it('classifies using the documented cut points (0.4 / 0.7 / 0.85)', () => {
    expect(classifyRiskTier(0)).toBe('low');
    expect(classifyRiskTier(0.39)).toBe('low');
    expect(classifyRiskTier(0.4)).toBe('moderate');
    expect(classifyRiskTier(0.69)).toBe('moderate');
    expect(classifyRiskTier(0.7)).toBe('high');
    expect(classifyRiskTier(0.84)).toBe('high');
    expect(classifyRiskTier(0.85)).toBe('critical');
    expect(classifyRiskTier(1)).toBe('critical');
  });
});

describe('normalizeAlertLevel', () => {
  it('maps every real backend alert level to the matching tier', () => {
    expect(normalizeAlertLevel('LOW')).toBe('low');
    expect(normalizeAlertLevel('MODERATE')).toBe('moderate');
    expect(normalizeAlertLevel('HIGH')).toBe('high');
    expect(normalizeAlertLevel('VERY_HIGH')).toBe('critical');
  });

  it('falls back to low for an unrecognized or missing level rather than throwing', () => {
    expect(normalizeAlertLevel('SOMETHING_NEW')).toBe('low');
    expect(normalizeAlertLevel(null)).toBe('low');
    expect(normalizeAlertLevel(undefined)).toBe('low');
  });
});

describe('tier lookups', () => {
  it('every tier has a color, emoji, and label — none silently undefined', () => {
    for (const tier of ['low', 'moderate', 'high', 'critical'] as const) {
      expect(tierColor(tier)).toMatch(/^#[0-9a-f]{6}$/i);
      expect(tierEmoji(tier)).not.toBe('');
      expect(tierLabel(tier)).not.toBe('');
    }
  });

  it('assigns a visually distinct color to every tier', () => {
    const tiers = ['low', 'moderate', 'high', 'critical'] as const;
    const colors = tiers.map(tierColor);
    expect(new Set(colors).size).toBe(tiers.length);
  });
});

describe('formatPercent', () => {
  it('formats a 0..1 fraction as a whole-number percent by default', () => {
    expect(formatPercent(0.163)).toBe('16%');
    expect(formatPercent(1)).toBe('100%');
    expect(formatPercent(0)).toBe('0%');
  });

  it('shows an em dash for missing or invalid values instead of "NaN%"', () => {
    expect(formatPercent(null)).toBe('—');
    expect(formatPercent(undefined)).toBe('—');
    expect(formatPercent(NaN)).toBe('—');
  });
});

describe('formatDuration', () => {
  it('picks the roughest sensible unit for the magnitude', () => {
    expect(formatDuration(30)).toBe('1m');
    expect(formatDuration(3600)).toBe('1.0h');
    expect(formatDuration(3600 * 72)).toBe('3.0d');
  });

  it('shows an em dash for missing values', () => {
    expect(formatDuration(null)).toBe('—');
    expect(formatDuration(undefined)).toBe('—');
  });
});

describe('computeTargetTimestamp', () => {
  it('adds exactly predictionHorizonHours to predictionTimestamp', () => {
    const target = computeTargetTimestamp({
      predictionTimestamp: '2026-01-01T00:00:00.000Z',
      predictionHorizonHours: 168,
    });
    expect(target.toISOString()).toBe('2026-01-08T00:00:00.000Z');
  });
});

describe('parseSceneId', () => {
  it('extracts platform, date, and time from a real Sentinel-1 scene id', () => {
    const parsed = parseSceneId('S1A_IW_GRDH_1SDV_20170808T122137_20170808T122202_017832_01DE48_D7D6');
    expect(parsed).toEqual({ id: expect.any(String), platform: 'S1A', date: '2017-08-08', time: '12:21' });
  });

  it('degrades gracefully for an id that does not match the expected pattern', () => {
    const parsed = parseSceneId('not-a-real-scene-id');
    expect(parsed.platform).toBe('—');
    expect(parsed.date).toBe('—');
    expect(parsed.time).toBe('—');
  });
});

describe('formatRelativeTime', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-01T00:10:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('buckets elapsed time into moments/minutes/hours/days', () => {
    expect(formatRelativeTime('2026-01-01T00:09:45.000Z')).toBe('moments ago');
    expect(formatRelativeTime('2026-01-01T00:05:00.000Z')).toBe('5m ago');
    expect(formatRelativeTime('2025-12-31T22:10:00.000Z')).toBe('2h ago');
    expect(formatRelativeTime('2025-12-29T00:10:00.000Z')).toBe('3d ago');
  });

  it('shows an em dash for a missing or invalid timestamp', () => {
    expect(formatRelativeTime(null)).toBe('—');
    expect(formatRelativeTime('not-a-date')).toBe('—');
  });
});
