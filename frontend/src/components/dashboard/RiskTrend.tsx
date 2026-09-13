import { useState } from 'react';
import { formatPercent, formatShortDate, formatTime, normalizeAlertLevel, tierColor, tierLabel } from '../../lib/format';
import type { RiskHistoryPoint } from '../../types/risk';
import styles from './RiskTrend.module.css';

const WIDTH = 320;
const HEIGHT = 84;
const PADDING = 8;

interface RiskTrendProps {
  points: RiskHistoryPoint[];
  /** 'compact' fits a small dashboard panel; 'full' fills a dedicated history page. */
  variant?: 'compact' | 'full';
}

export function RiskTrend({ points, variant = 'compact' }: RiskTrendProps) {
  const [hover, setHover] = useState<number | null>(null);

  if (points.length === 0) {
    return <p className={styles.empty}>No readings recorded yet.</p>;
  }

  const values = points.map((p) => p.mean);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0.2);
  const span = max - min || 1;

  const coords = points.map((point, index) => {
    const x = points.length === 1 ? WIDTH / 2 : PADDING + (index / (points.length - 1)) * (WIDTH - PADDING * 2);
    const y = HEIGHT - PADDING - ((point.mean - min) / span) * (HEIGHT - PADDING * 2);
    return { x, y, point };
  });

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x},${c.y}`).join(' ');
  const areaPath = `${linePath} L${coords[coords.length - 1].x},${HEIGHT} L${coords[0].x},${HEIGHT} Z`;
  const last = points[points.length - 1];
  const lastColor = tierColor(normalizeAlertLevel(last.alertLevel));
  const hovered = hover != null ? coords[hover] : null;

  return (
    <div className={styles.wrap} data-variant={variant} onMouseLeave={() => setHover(null)}>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className={styles.svg} preserveAspectRatio="none">
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lastColor} stopOpacity="0.35" />
            <stop offset="100%" stopColor={lastColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#trendFill)" />
        <path d={linePath} fill="none" stroke={lastColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {coords.map((c, i) => (
          <circle
            key={c.point.predictionId}
            cx={c.x}
            cy={c.y}
            r={hover === i ? 4.5 : 2.4}
            fill={tierColor(normalizeAlertLevel(c.point.alertLevel))}
            className={styles.point}
            onMouseEnter={() => setHover(i)}
            onFocus={() => setHover(i)}
            onBlur={() => setHover(null)}
            tabIndex={0}
            role="img"
            aria-label={`${formatShortDate(c.point.predictionTimestamp)}: ${formatPercent(c.point.mean)} mean risk, ${tierLabel(normalizeAlertLevel(c.point.alertLevel))}`}
          />
        ))}
      </svg>

      {hovered && (
        <div
          className={styles.tooltip}
          style={{ left: `${(hovered.x / WIDTH) * 100}%`, top: `${(hovered.y / HEIGHT) * 100}%` }}
        >
          <strong>{formatPercent(hovered.point.mean)}</strong>
          <span>{tierLabel(normalizeAlertLevel(hovered.point.alertLevel))}</span>
          <span>
            {formatShortDate(hovered.point.predictionTimestamp)} · {formatTime(hovered.point.predictionTimestamp)}
          </span>
        </div>
      )}

      <div className={styles.range}>
        <span>
          {formatShortDate(points[0].predictionTimestamp)} · {formatTime(points[0].predictionTimestamp)}
        </span>
        <span>
          {formatShortDate(last.predictionTimestamp)} · {formatTime(last.predictionTimestamp)}
        </span>
      </div>
    </div>
  );
}
