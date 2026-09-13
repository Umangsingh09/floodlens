import { EventCard } from '../components/history/EventCard';
import type { HistoricalEvent } from '../types/events';
import styles from './EventsPage.module.css';

interface EventsPageProps {
  events: HistoricalEvent[];
  loading: boolean;
}

export function EventsPage({ events, loading }: EventsPageProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.pageHead}>
        <span className={styles.eyebrow}>Validation record</span>
        <h1 className={styles.heading}>Checked against real historical floods</h1>
        <p className={styles.lede}>
          Predictions are only trustworthy if they line up with what actually happened. Each
          entry below is a real, satellite-derived flood event used to validate spatial output —
          never used to train the model itself.
        </p>
      </div>

      {loading ? (
        <div className={styles.skeleton} />
      ) : events.length === 0 ? (
        <div className={styles.empty}>
          <p>No validated reference events yet.</p>
        </div>
      ) : (
        <div className={styles.page}>
          {events.map((event) => (
            <EventCard key={event.dfoId} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}
