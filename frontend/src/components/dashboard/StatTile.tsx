import styles from './StatTile.module.css';

interface StatTileProps {
  label: string;
  value: string;
  caption?: string;
}

export function StatTile({ label, value, caption }: StatTileProps) {
  return (
    <div className={styles.tile}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{value}</span>
      {caption && <span className={styles.caption}>{caption}</span>}
    </div>
  );
}
