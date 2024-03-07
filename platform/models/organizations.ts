export interface UsageQuota {
  org_id: string;
  plan: string;
  current_usage: number;
  max_usage: number;
  max_usage_label: string;
}

export interface OrgMetadata {
  org_id: string;
  plan?: string | null; // "hobby" or "pro"
  customer_id?: string | null; // Stripe customer id
  initialized?: boolean | null; // Whether the org has been initialized
}
