import { computeTargetTimestamp, formatDuration, formatShortDate, formatTime } from '../../lib/format';
import type { RiskSnapshot } from '../../types/risk';
import styles from './PipelineSteps.module.css';

export function PipelineSteps({ risk }: { risk: RiskSnapshot }) {
  const targetDate = computeTargetTimestamp(risk);

  const steps = [
    {
      label: 'Satellite pass',
      value: `${formatShortDate(risk.sourcePassTimestamp)} · ${formatTime(risk.sourcePassTimestamp)}`,
      detail: risk.satellite,
    },
    {
      label: 'Processing lag',
      value: formatDuration(risk.processingLagSeconds),
      detail: 'pass to prediction',
    },
    {
      label: 'Prediction generated',
      value: `${formatShortDate(risk.predictionTimestamp)} · ${formatTime(risk.predictionTimestamp)}`,
      detail: `model ${risk.modelVersion}`,
    },
    {
      label: 'Outlook target',
      value: formatShortDate(targetDate.toISOString()),
      detail: `+${Math.round(risk.predictionHorizonHours / 24)}d horizon`,
    },
  ];

  return (
    <div className={styles.track}>
      {steps.map((step, index) => (
        <div key={step.label} className={styles.step}>
          <div className={styles.dotRow}>
            <span className={styles.dot} />
            {index < steps.length - 1 && <span className={styles.connector} />}
          </div>
          <span className={styles.label}>{step.label}</span>
          <span className={styles.value}>{step.value}</span>
          <span className={styles.detail}>{step.detail}</span>
        </div>
      ))}
    </div>
  );
}
