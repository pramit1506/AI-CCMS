export type ToolStatus = 'idle' | 'executing' | 'success' | 'error';

export interface TimelineEvent {
  id: string;
  timestamp: string;
  title: string;
  description?: string;
  status: ToolStatus;
}

export interface ClarificationPayload {
  required: boolean;
  question?: string;
  options?: string[];
  field_name?: string;
}

export interface ToolExecutionEvent {
  tool_name: string;
  status: ToolStatus;
  input?: any;
  result?: any;
  error?: string;
}

// Backend Schemas

export enum ConversationStatus {
  COLLECTING_INFORMATION = "COLLECTING_INFORMATION",
  AWAITING_CLARIFICATION = "AWAITING_CLARIFICATION",
  READY_FOR_EXECUTION = "READY_FOR_EXECUTION",
  EXECUTING_TOOL = "EXECUTING_TOOL",
  COMPLETED = "COMPLETED"
}

export interface ToolExecutionResult {
  status: string;
  created_resource_id?: string;
  success_message?: string;
  validation_warnings?: string[];
}

export interface ClarificationState {
  tool_name: string;
  required_fields: string[];
  missing_fields: string[];
  resolved_fields: Record<string, any>;
  clarification_reason?: string;
  original_request: string;
  status?: string;
  is_active: boolean;
}

export interface DecisionOutput {
  action: string;
  tool_readiness: string;
  selected_tool?: string;
  clarification_message?: string;
  clarification_reason?: string;
  required_missing_fields: string[];
  optional_missing_fields: string[];
  decision_confidence: number;
  next_state: string;
}

export interface ConversationMetadata {
  active_hcp?: string;
  active_hospital?: string;
  active_interaction?: string;
  last_followup?: string;
  last_tool?: string;
  conversation_start: string;
  last_activity: string;
  message_count: number;
  estimated_tokens: number;
}

export interface AgentState {
  graphExecutionId: string | null;
  selectedTool: string | null;
  toolStatus: ToolStatus;
  clarificationRequired: ClarificationPayload | null;
  currentStep: string | null;
  executionTimeline: TimelineEvent[];
  lastToolResult: any | null;
  conversationStatus?: ConversationStatus;
}
