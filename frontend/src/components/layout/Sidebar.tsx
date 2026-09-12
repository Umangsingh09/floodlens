import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { label: 'Dashboard', active: true },
  { label: 'Risk Map', active: false },
  { label: 'Historical Events', active: false },
  { label: 'Alerts', active: false },
];

export function Sidebar() {
  return (
    <nav className={styles.sidebar}>
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
        Navigation is a placeholder. Only the Dashboard is currently wired up.
      </p>
    </nav>
  );
}
