import type { ReactNode } from 'react';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import styles from './AppLayout.module.css';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className={styles.shell}>
      <Header />
      <div className={styles.body}>
        <Sidebar />
        <main className={styles.content}>{children}</main>
      </div>
    </div>
  );
}
