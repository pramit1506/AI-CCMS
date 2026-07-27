export enum ComplaintStatus {
  PENDING_TRIAGE = 'PENDING_TRIAGE',
  IN_PROGRESS = 'IN_PROGRESS',
  CLOSED = 'CLOSED'
}

export enum ComplaintSource {
  EMAIL = 'EMAIL',
  CALL = 'CALL',
  PDF = 'PDF',
  PORTAL = 'PORTAL',
  TEXT = 'TEXT'
}

export enum Severity {
  CRITICAL = 'CRITICAL',
  MAJOR = 'MAJOR',
  MINOR = 'MINOR'
}

export enum Priority {
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW'
}

export enum DraftStatus {
  EMPTY = 'EMPTY',
  PARTIAL = 'PARTIAL',
  READY = 'READY',
  CONFIRMED = 'CONFIRMED',
  SAVED = 'SAVED'
}

export interface FieldMetadata {
  value?: any;
  confidence?: number;
  source?: string;
  last_updated?: string;
}

export interface ComplaintDraft {
  customer_id?: string;
  customer_name?: string;
  complaint_source?: ComplaintSource;
  product_name?: string;
  product_strength?: string;
  batch_number?: string;
  manufacturing_date?: string;
  expiry_date?: string;
  quantity_affected?: string;
  complaint_type?: string;
  complaint_date?: string;
  detailed_description?: string;
  initial_severity?: Severity;
  priority?: Priority;
  status?: ComplaintStatus;
  risk_classification?: string;
  root_cause_recommendation?: string;
  capa_recommendation?: string;
  risk_reasoning?: string;
  confidence_scores?: Record<string, number>;
  field_metadata?: Record<string, FieldMetadata>;
}
