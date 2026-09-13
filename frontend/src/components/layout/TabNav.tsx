import styles from './TabNav.module.css';

export type TabKey = 'dashboard' | 'map' | 'events' | 'history' | 'about';

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'map', label: 'Risk Map' },
  { key: 'events', label: 'Events' },
  { key: 'history', label: 'History' },
  { key: 'about', label: 'About/Data' },
];

interface TabNavProps {
  active: TabKey;
  onChange: (tab: TabKey) => void;
}

export function TabNav({ active, onChange }: TabNavProps) {
  return (
    <nav className={styles.wrap} aria-label="Sections">
      <div className={styles.track}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={styles.tab}
            data-active={tab.key === active}
            aria-current={tab.key === active ? 'page' : undefined}
            onClick={() => onChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
