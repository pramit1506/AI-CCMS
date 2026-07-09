import { ToolExecutionEvent, ClarificationPayload, ToolExecutionResult, ClarificationState, DecisionOutput, ConversationStatus, ConversationMetadata } from './agent';
import { InteractionDraft, DraftStatus } from './interaction';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_executions?: ToolExecutionEvent[];
  clarification_request?: ClarificationPayload;
}

export interface ChatRequest {
  user_message: string;
  conversation_id?: string;
  message_history: { role: string; content: string }[];
}

export interface FieldChange {
  field_name: string;
  previous_value?: any;
  current_value?: any;
  change_type: string;
}

export interface ConversationResponse {
  assistant_message: string;
  conversation_id: string;
  interaction_draft?: InteractionDraft;
  draft_status?: DraftStatus;
  draft_changes: FieldChange[];
  clarification_state?: ClarificationState;
  decision_output?: DecisionOutput;
  tool_execution_result?: ToolExecutionResult;
  conversation_status: ConversationStatus;
  conversation_metadata?: ConversationMetadata;
}
