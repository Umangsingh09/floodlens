import type { ReactNode } from 'react';
import styles from './AppLayout.module.css';

interface AppLayoutProps {
  header: ReactNode;
  tabs: ReactNode;
  children: ReactNode;
}

export function AppLayout({ header, tabs, children }: AppLayoutProps) {
  return (
    <div className={styles.shell}>
      {header}
      {tabs}
      <main className={styles.content}>{children}</main>
    </div>
  );
}
