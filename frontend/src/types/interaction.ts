export enum InteractionStatus {
  PLANNED = 'PLANNED',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
  NO_SHOW = 'NO_SHOW'
}

export enum InteractionType {
  EMAIL = 'EMAIL',
  IN_PERSON = 'IN_PERSON',
  VIRTUAL = 'VIRTUAL',
  PHONE = 'PHONE'
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

export interface InteractionDraft {
  hcp_id?: string;
  hcp_name?: string;
  interaction_type?: InteractionType;
  interaction_date?: string;
  interaction_time?: string;
  discussion_summary?: string;
  topics_discussed?: string[];
  materials_shared?: string[];
  sentiment?: string;
  follow_up_required?: boolean;
  follow_up_date?: string;
  attendees?: string[];
  status?: InteractionStatus;
  confidence_scores?: Record<string, number>;
  field_metadata?: Record<string, FieldMetadata>;
}
