import type { ReactNode } from 'react';
import styles from './Panel.module.css';

interface PanelProps {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  children: ReactNode;
  span?: 'narrow' | 'wide' | 'full';
}

export function Panel({ icon, title, subtitle, children, span = 'narrow' }: PanelProps) {
  return (
    <section className={styles.panel} data-span={span}>
      <header className={styles.header}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <div>
          <h3 className={styles.title}>{title}</h3>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
      </header>
      <div className={styles.body}>{children}</div>
    </section>
  );
}
