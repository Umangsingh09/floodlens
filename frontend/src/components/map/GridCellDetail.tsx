import { useEffect } from 'react';
import {
  classifyRiskTier,
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
  const targetDate = new Date(
    new Date(risk.predictionTimestamp).getTime() + risk.predictionHorizonHours * 3600 * 1000,
  );
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
      </dl>

      <p className={styles.note}>
        Environmental features (elevation, water history) that feed the model aren't exposed
        per-cell by the current API — only the aggregate risk score above is.
      </p>
    </div>
  );
}
