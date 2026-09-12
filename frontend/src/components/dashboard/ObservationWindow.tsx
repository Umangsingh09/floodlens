import { parseSceneId } from '../../lib/format';
import styles from './ObservationWindow.module.css';

const STEP_LABELS = ['t − 2', 't − 1', 't (current)'];

export function ObservationWindow({ scenes }: { scenes: string[] }) {
  return (
    <ol className={styles.list}>
      {scenes.map((sceneId, index) => {
        const parsed = parseSceneId(sceneId);
        const label = STEP_LABELS[index] ?? `t − ${scenes.length - 1 - index}`;
        return (
          <li key={sceneId} className={styles.row}>
            <span className={styles.step}>{label}</span>
            <span className={styles.date}>{parsed.date}</span>
            <span className={styles.time}>{parsed.time} UTC</span>
            <span className={styles.platform}>{parsed.platform}</span>
          </li>
        );
      })}
    </ol>
  );
}
