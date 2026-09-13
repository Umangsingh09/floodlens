import { Component, type ErrorInfo, type ReactNode } from 'react';
import styles from './AppErrorBoundary.module.css';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class AppErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('FloodLens UI crashed:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className={styles.wrap}>
          <h1 className={styles.heading}>Something went wrong rendering this page</h1>
          <p className={styles.message}>
            This is a UI error, not a data or backend problem — reloading usually clears it.
          </p>
          <pre className={styles.detail}>{this.state.error.message}</pre>
          <button type="button" className={styles.retry} onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
