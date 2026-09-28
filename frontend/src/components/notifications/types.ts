export interface NotificationPreference {
  id: string;
  user_id: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
  push_enabled: boolean;
  email_address?: string | null;
  push_token?: string | null;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  event_overrides: Record<string, Record<string, boolean>>;
  created_at: string;
  updated_at: string;
}

export interface NotificationTemplate {
  id: string;
  event_type: string;
  name: string;
  description?: string | null;
  title_template: string;
  in_app_template: string;
  email_subject_template?: string | null;
  email_body_template?: string | null;
  push_title_template?: string | null;
  push_body_template?: string | null;
  default_priority: 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationEvent {
  id: string;
  event_type: string;
  organization_id?: string | null;
  user_id?: string | null;
  idempotency_key?: string | null;
  payload: Record<string, any>;
  channels: string[];
  status: 'PENDING' | 'DELIVERED' | 'PARTIALLY_DELIVERED' | 'FAILED' | 'RETRYING' | 'DEDUPLICATED' | 'SUPPRESSED_QUIET_HOURS';
  attempts: number;
  max_retries: number;
  last_error?: string | null;
  rendered_title?: string | null;
  rendered_body?: string | null;
  channel_delivery_results: Record<string, any>;
  created_at: string;
  sent_at?: string | null;
  next_retry_at?: string | null;
}

export interface NotificationDeliveryStats {
  total_events: number;
  delivered_events: number;
  failed_events: number;
  retrying_events: number;
  deduplicated_events: number;
  suppressed_quiet_hours: number;
  channel_counts: Record<string, number>;
  success_rate_pct: number;
  average_attempts: number;
}
