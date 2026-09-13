import { useEffect } from 'react';
import {
  classifyRiskTier,
  computeTargetTimestamp,
  formatDuration,
  formatPercent,
  formatShortDate,
  formatTime,
  tierColor,
  tierEmoji,
  tierLabel,
} from '../../lib/format';
import type { RiskGridCell, RiskSnapshot } from '../../types/risk';
import styles from './GridCellDetail.module.css';

interface GridCellDetailProps {
  cell: RiskGridCell;
  risk: RiskSnapshot;
  onClose: () => void;
}

export function GridCellDetail({ cell, risk, onClose }: GridCellDetailProps) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const tier = classifyRiskTier(cell.value);
  const targetDate = computeTargetTimestamp(risk);
  const sceneCount = risk.observationWindowScenes?.length ?? 0;

  return (
    <div className={styles.panel} role="dialog" aria-label="Grid cell detail">
      <div className={styles.header}>
        <span className={styles.badge} style={{ color: tierColor(tier), borderColor: tierColor(tier) }}>
          {tierEmoji(tier)} {tierLabel(tier)}
        </span>
        <button type="button" className={styles.close} onClick={onClose} aria-label="Close detail panel">
          ×
        </button>
      </div>

      <div className={styles.score}>{formatPercent(cell.value)}</div>
      <div className={styles.coords}>
        {cell.lat.toFixed(4)}°, {cell.lon.toFixed(4)}°
      </div>

      <div className={styles.divider} />

      <div className={styles.sectionLabel}>Prediction context</div>
      <dl className={styles.meta}>
        <div className={styles.row}>
          <dt>Satellite pass</dt>
          <dd>
            {risk.satellite} · {formatShortDate(risk.sourcePassTimestamp)} {formatTime(risk.sourcePassTimestamp)}
          </dd>
        </div>
        <div className={styles.row}>
          <dt>Observations used</dt>
          <dd>{sceneCount > 0 ? `${sceneCount} Sentinel-1 passes` : 'not recorded'}</dd>
        </div>
        <div className={styles.row}>
          <dt>Prediction generated</dt>
          <dd>
            {formatShortDate(risk.predictionTimestamp)} {formatTime(risk.predictionTimestamp)}
          </dd>
        </div>
        <div className={styles.row}>
          <dt>Outlook target</dt>
          <dd>{formatShortDate(targetDate.toISOString())}</dd>
        </div>
        <div className={styles.row}>
          <dt>Processing lag</dt>
          <dd>{formatDuration(risk.processingLagSeconds)}</dd>
        </div>
        <div className={styles.row}>
          <dt>Model</dt>
          <dd>
            {risk.modelId} · {risk.modelVersion}
          </dd>
        </div>
        {risk.weatherContext && (
          <div className={styles.row}>
            <dt>Regional weather</dt>
            <dd>
              {risk.weatherContext.rainfall7dMm.toFixed(0)}mm rain (7d) ·{' '}
              {risk.weatherContext.soilMoistureSurface.toFixed(2)} soil moisture
            </dd>
          </div>
        )}
      </dl>

      <p className={styles.note}>
        Elevation, water history, and weather feed the model but aren't exposed per-cell by the
        current API — the regional weather reading above (and the risk score) are the exceptions.
      </p>
    </div>
  );
}
