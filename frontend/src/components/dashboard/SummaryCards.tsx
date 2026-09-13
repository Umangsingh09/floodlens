import {
  classifyRiskTier,
  formatPercent,
  formatRelativeTime,
  formatShortDate,
  formatTime,
  normalizeAlertLevel,
  tierColor,
  tierEmoji,
  tierLabel,
  type RiskTier,
} from '../../lib/format';
import type { RiskGrid, RiskSnapshot } from '../../types/risk';
import styles from './SummaryCards.module.css';

interface SummaryCardsProps {
  risk: RiskSnapshot | null;
  grid: RiskGrid | null;
  gridLoading: boolean;
  eventCount: number;
  eventsLoading: boolean;
}

interface Card {
  label: string;
  value: string;
  caption: string;
  tier?: RiskTier;
}

export function SummaryCards({ risk, grid, gridLoading, eventCount, eventsLoading }: SummaryCardsProps) {
  const meanTier = risk ? normalizeAlertLevel(risk.alert.level) : undefined;

  const cells = grid?.cells ?? [];
  const peakCell = cells.reduce<(typeof cells)[number] | null>(
    (max, cell) => (max === null || cell.value > max.value ? cell : max),
    null,
  );
  const peakTier = peakCell ? classifyRiskTier(peakCell.value) : undefined;
  const highRiskCount = cells.filter((c) => ['high', 'critical'].includes(classifyRiskTier(c.value))).length;
  const gridPending = Boolean(risk) && gridLoading;

  const cards: Card[] = [
    {
      label: 'Current flood risk',
      value: risk ? formatPercent(risk.risk.mean) : '—',
      caption: risk ? `${tierEmoji(meanTier!)} ${tierLabel(meanTier!)} · mean across grid` : 'No prediction has run yet',
      tier: meanTier,
    },
    {
      label: 'Peak risk cell',
      value: gridPending ? '…' : peakCell ? formatPercent(peakCell.value) : '—',
      caption: gridPending
        ? 'Loading grid…'
        : peakCell
          ? `${peakCell.lat.toFixed(2)}°, ${peakCell.lon.toFixed(2)}°`
          : 'No grid data yet',
      tier: peakTier,
    },
    {
      label: 'High-risk cells',
      value: gridPending ? '…' : cells.length > 0 ? `${highRiskCount} / ${cells.length}` : '—',
      caption: gridPending ? 'Loading grid…' : 'High + Critical tiers in the current grid',
      tier: cells.length > 0 ? (highRiskCount > 0 ? 'high' : 'low') : undefined,
    },
    {
      label: 'Validated historical events',
      value: eventsLoading ? '…' : String(eventCount),
      caption: 'Used to validate spatial output — not to train the model',
    },
    {
      label: 'Last data update',
      value: risk ? formatRelativeTime(risk.predictionTimestamp) : '—',
      caption: risk
        ? `Satellite pass ${formatShortDate(risk.sourcePassTimestamp)} ${formatTime(risk.sourcePassTimestamp)}`
        : 'No observation pass recorded yet',
    },
    {
      label: 'Prediction horizon',
      value: risk ? `${Math.round(risk.predictionHorizonHours / 24)}d` : '—',
      caption: risk ? `${risk.predictionHorizonHours}h ahead of the observation` : 'Set once a prediction has run',
    },
  ];

  return (
    <div className={styles.row}>
      {cards.map((card) => (
        <div
          key={card.label}
          className={styles.card}
          style={card.tier ? { borderTopColor: tierColor(card.tier) } : undefined}
        >
          <span className={styles.label}>{card.label}</span>
          <span className={styles.value}>{card.value}</span>
          <span className={styles.caption}>{card.caption}</span>
        </div>
      ))}
    </div>
  );
}
