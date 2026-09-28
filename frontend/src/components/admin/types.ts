/**
 * FoodLoop AI - Super Admin Types & Contracts (Phase 16)
 */

export interface AdminOverviewKpis {
  total_organizations: number;
  active_kitchens: number;
  processing_units: number;
  registered_recipients: number;
  food_rescued_kg: number;
  waste_generated_kg: number;
  waste_reduction_pct: number;
  successful_donations: number;
  active_deliveries: number;
  people_served: number;
  estimated_value_preserved_usd: number;
  calculated_at?: string;
}

export type AdminMapNodeType = 'KITCHEN' | 'PROCESSING_UNIT' | 'RECIPIENT' | 'COURIER';

export interface AdminMapNode {
  id: string;
  name: string;
  node_type: AdminMapNodeType;
  latitude: number;
  longitude: number;
  address?: string;
  status: string;
  contact_phone?: string;
  organization_name?: string;
  details: Record<string, any>;
}

export type AlertCategory =
  | 'expired_surplus'
  | 'failed_delivery'
  | 'abnormal_waste_increase'
  | 'model_failure'
  | 'low_prediction_confidence'
  | 'system_errors';

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface AdminAlert {
  id: string;
  category: AlertCategory;
  severity: AlertSeverity;
  title: string;
  message: string;
  entity_type?: string;
  entity_id?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface AdminAlertsSummary {
  total_active_alerts: number;
  by_category: Record<AlertCategory, number>;
  alerts: AdminAlert[];
}

export interface AdminOrg {
  id: string;
  name: string;
  org_type: string;
  registration_number: string;
  is_active: boolean;
  is_verified: boolean;
  contact_email: string;
  contact_phone: string;
  kitchens_count: number;
  fpus_count: number;
  members_count: number;
  created_at: string;
}

export interface AdminRecipient {
  id: string;
  name: string;
  facility_type: string;
  address: string;
  verified_charity_id?: string;
  contact_person?: string;
  contact_phone?: string;
  max_daily_intake_kg: number;
  cold_storage_available: boolean;
  verification_status: 'VERIFIED' | 'PENDING' | 'REJECTED';
  is_active: boolean;
  reliability_score: number;
  created_at: string;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  organization_name?: string;
  created_at: string;
}

export interface BusinessRule {
  id: string;
  rule_key: string;
  rule_name: string;
  category: string;
  value: any;
  description?: string;
  is_active: boolean;
  updated_at: string;
}

export interface ModelMetricDetail {
  model_name: string;
  version: string;
  task: 'DEMAND_FORECAST' | 'WASTE_PREDICTION' | 'COMPUTER_VISION' | string;
  status: 'OPTIMAL' | 'DRIFT_DETECTED' | 'DEGRADED';
  r2_score?: number;
  mae?: number;
  rmse?: number;
  accuracy_pct?: number;
  mean_confidence?: number;
  low_confidence_pct?: number;
  inference_latency_ms: number;
  total_predictions_analyzed: number;
  last_updated: string;
}

export interface AdminModelPerformance {
  overall_health: 'OPTIMAL' | 'ATTENTION_REQUIRED' | 'CRITICAL';
  models: ModelMetricDetail[];
}

export interface AuditLogItem {
  id: string;
  organization_id?: string;
  user_id?: string;
  user_email: string;
  user_name: string;
  module: string;
  action: string;
  entity_name: string;
  entity_id: string;
  old_values?: any;
  new_values?: any;
  client_ip?: string;
  sha256_hash: string;
  is_hash_valid: boolean;
  created_at: string;
}

export interface AdminAuditLogsResponse {
  total: number;
  page: number;
  size: number;
  items: AuditLogItem[];
}
