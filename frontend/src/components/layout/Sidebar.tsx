import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { label: 'Dashboard', active: true },
  { label: 'Risk Map', active: false },
  { label: 'Historical Events', active: false },
  { label: 'Alerts', active: false },
  { label: 'Data Sources', active: false },
];

export function Sidebar() {
  return (
    <nav className={styles.sidebar} aria-label="Sidebar navigation">
      <div className={styles.sectionLabel}>Operations</div>
      <ul className={styles.list}>
        {NAV_ITEMS.map((item) => (
          <li
            key={item.label}
            className={styles.item}
            data-active={item.active}
          >
            {item.label}
          </li>
        ))}
      </ul>
      <p className={styles.note}>
        Placeholder navigation. Future routes will be connected once the risk
        backend and dashboard workflows are finalized.
      </p>
    </nav>
  );
}
