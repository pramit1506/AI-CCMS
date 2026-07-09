import { ConversationResponse } from '../types/chat';
import { ClarificationPayload, ToolExecutionEvent } from '../types/agent';
import { InteractionDraft } from '../types/interaction';

export interface MappedConversation {
  assistantMessage: string;
  conversationId: string;
  interactionDraft: InteractionDraft | null;
  updatedFields: string[];
  clarificationRequired: ClarificationPayload | null;
  toolExecution: ToolExecutionEvent | null;
  conversationStatus: string;
}

export const conversationMapper = {
  mapResponse(response: ConversationResponse): MappedConversation {
    const legacyResponse = response as any;
    const assistantMessage = response.assistant_message || legacyResponse.response || '';
    const interactionDraft = response.interaction_draft || legacyResponse.interaction_updates || null;
    const draftChanges = response.draft_changes || [];

    let clarificationRequired: ClarificationPayload | null = null;
    
    const clarificationState = response.clarification_state;
    const clarificationIsActive = Boolean(
      clarificationState &&
      (clarificationState.is_active ||
        ['CREATED', 'ACTIVE', 'UPDATED'].includes(clarificationState.status || ''))
    );

    if (clarificationState && clarificationIsActive) {
      clarificationRequired = {
        required: true,
        question:
          response.decision_output?.clarification_message ||
          clarificationState.clarification_reason ||
          'Please clarify your request.',
        options: [], // Frontend ClarificationCard uses options if provided
        field_name: clarificationState.missing_fields.length > 0 ? clarificationState.missing_fields[0] : undefined
      };
    }

    let toolExecution: ToolExecutionEvent | null = null;
    if (response.tool_execution_result) {
      // Backend status might be "success", "failed", or "error". Map to ToolStatus.
      const statusStr = response.tool_execution_result.status?.toLowerCase();
      const status = statusStr === 'success' ? 'success' : 'error';
      
      toolExecution = {
        tool_name: response.conversation_metadata?.last_tool || response.decision_output?.selected_tool || 'System Tool',
        status: status as 'success' | 'error',
        result: response.tool_execution_result.success_message || response.tool_execution_result.created_resource_id,
        error: response.tool_execution_result.validation_warnings?.length ? response.tool_execution_result.validation_warnings.join(', ') : undefined
      };
    } else if (legacyResponse.tool_executions?.length) {
      const legacyExecution = legacyResponse.tool_executions[0];
      toolExecution = {
        tool_name: legacyExecution.tool_name || 'System Tool',
        status: legacyExecution.status === 'success' ? 'success' : 'error',
        result: legacyExecution.result,
        error: legacyExecution.error
      };
    }

    const updatedFields = draftChanges.length
      ? draftChanges.map(change => change.field_name)
      : legacyResponse.interaction_updates
        ? Object.keys(legacyResponse.interaction_updates).filter((key) => legacyResponse.interaction_updates[key] !== null)
        : [];

    return {
      assistantMessage,
      conversationId: response.conversation_id,
      interactionDraft,
      updatedFields,
      clarificationRequired,
      toolExecution,
      conversationStatus: response.conversation_status
    };
  }
};
