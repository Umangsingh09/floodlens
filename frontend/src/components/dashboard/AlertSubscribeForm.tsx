import { useState, type FormEvent } from 'react';
import { useAlertCount } from '../../hooks/useAlertCount';
import { useAlertSubscription } from '../../hooks/useAlertSubscription';
import styles from './AlertSubscribeForm.module.css';

export function AlertSubscribeForm() {
  const { subscriptionId, subscribing, error, subscribe, unsubscribe } = useAlertSubscription();
  const count = useAlertCount(subscriptionId);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [thresholdPercent, setThresholdPercent] = useState(70);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!webhookUrl.trim()) return;
    subscribe(webhookUrl.trim(), thresholdPercent / 100);
  };

  if (subscriptionId) {
    return (
      <div className={styles.subscribed}>
        <p className={styles.status}>
          ✅ Subscribed — you'll get a webhook POST when mean risk crosses your threshold.
        </p>
        <button type="button" className={styles.unsubscribe} onClick={unsubscribe} disabled={subscribing}>
          {subscribing ? 'Removing…' : 'Unsubscribe'}
        </button>
      </div>
    );
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.field}>
        <label htmlFor="webhook-url">Webhook URL</label>
        <input
          id="webhook-url"
          type="url"
          required
          placeholder="https://hooks.slack.com/services/…"
          value={webhookUrl}
          onChange={(e) => setWebhookUrl(e.target.value)}
        />
        <span className={styles.hint}>
          A Slack/Discord incoming webhook, a Zapier/IFTTT catch hook, or any URL that accepts a
          POST. No email is sent — there's no email provider configured for this deployment.
        </span>
      </div>

      <div className={styles.field}>
        <label htmlFor="threshold">Notify when mean risk reaches</label>
        <div className={styles.thresholdRow}>
          <input
            id="threshold"
            type="range"
            min={0}
            max={100}
            step={5}
            value={thresholdPercent}
            onChange={(e) => setThresholdPercent(Number(e.target.value))}
          />
          <span className={styles.thresholdValue}>{thresholdPercent}%</span>
        </div>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <button type="submit" className={styles.submit} disabled={subscribing}>
        {subscribing ? 'Subscribing…' : 'Subscribe'}
      </button>

      {count != null && count > 0 && (
        <p className={styles.count}>
          {count} active subscription{count === 1 ? '' : 's'} right now.
        </p>
      )}
    </form>
  );
}
