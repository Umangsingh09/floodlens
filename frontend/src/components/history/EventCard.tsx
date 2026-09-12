import { formatDate } from '../../lib/format';
import type { HistoricalEvent } from '../../types/events';
import styles from './EventCard.module.css';

export function EventCard({ event }: { event: HistoricalEvent }) {
  const countries = event.countries.split(',').map((c) => c.trim());

  return (
    <article className={styles.card}>
      <div className={styles.header}>
        <span className={styles.badge}>DFO {event.dfoId}</span>
        <span className={styles.dates}>
          {formatDate(event.startDate)} – {formatDate(event.endDate)}
        </span>
      </div>

      <h3 className={styles.title}>{event.primaryCountry} flood reference</h3>

      <div className={styles.chips}>
        {countries.map((country) => (
          <span key={country} className={styles.chip}>
            {country}
          </span>
        ))}
      </div>

      <div className={styles.formula}>
        <code>flood_reference = flooded == 1 &amp;&amp; permanent_water == 0</code>
      </div>

      <p className={styles.footnote}>
        {event.resolutionMeters}m satellite-derived reference · used to validate spatial
        predictions against a real historical flood, not as model training ground truth.
      </p>
    </article>
  );
}
