export interface AlertSubscription {
  id: string;
  webhookUrl: string;
  threshold: number;
  createdAt: string;
}

export interface AlertSubscriptionCount {
  count: number;
}
