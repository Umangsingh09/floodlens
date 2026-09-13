import { useEffect, useState } from 'react';
import { ALERT_LABELS, normalizeAlertLevel, formatPercent, tierColor } from '../../lib/format';
import styles from './RiskGauge.module.css';

interface RiskGaugeProps {
  value: number;
  alertLevel: string;
}

const RADIUS = 54;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function RiskGauge({ value, alertLevel }: RiskGaugeProps) {
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setAnimated(value));
    return () => cancelAnimationFrame(frame);
  }, [value]);

  // Colored by the backend's own alert level, not re-derived from the raw value — so the
  // arc color always agrees with the label sitting right beside it.
  const color = tierColor(normalizeAlertLevel(alertLevel));
  const offset = CIRCUMFERENCE * (1 - Math.max(0, Math.min(1, animated)));

  return (
    <div className={styles.wrap}>
      <svg viewBox="0 0 120 120" className={styles.svg} role="img" aria-label={`Mean risk ${formatPercent(value)}`}>
        <circle cx="60" cy="60" r={RADIUS} className={styles.track} />
        <circle
          cx="60"
          cy="60"
          r={RADIUS}
          className={styles.arc}
          style={{
            stroke: color,
            strokeDasharray: CIRCUMFERENCE,
            strokeDashoffset: offset,
          }}
        />
      </svg>
      <div className={styles.center}>
        <span className={styles.value}>{formatPercent(value)}</span>
        <span className={styles.label} style={{ color }}>
          {ALERT_LABELS[alertLevel] ?? alertLevel}
        </span>
      </div>
    </div>
  );
}
