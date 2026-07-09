from typing import Any, Dict
from app.schemas.chat import ConversationResponse, FieldChange, ToolExecutionResult
from app.shared.enums import ConversationStatus, AgentState
from app.schemas.memory import ConversationMetadata

class ConversationResponseMapper:
    @staticmethod
    def _stringify_optional(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def map_to_response(final_state: Dict[str, Any]) -> ConversationResponse:
        # Extract fields from final_state
        draft = final_state.get("interaction_draft")
        draft_status = final_state.get("draft_status")
        changed_fields_list = final_state.get("changed_fields") or []
        
        field_changes = []
        if draft and changed_fields_list:
            draft_dict = draft.model_dump()
            for field in changed_fields_list:
                current_val = draft_dict.get(field)
                change_type = "added"
                if current_val is None or (isinstance(current_val, list) and len(current_val) == 0):
                    change_type = "removed"
                else:
                    change_type = "updated"
                
                field_changes.append(
                    FieldChange(
                        field_name=field,
                        previous_value=None,  # We don't have access to the old value from just final_state
                        current_value=current_val,
                        change_type=change_type
                    )
                )

        # Map ToolExecutionResult
        tool_status = final_state.get("tool_status")
        tool_result = final_state.get("tool_result")
        validation_errors = final_state.get("validation_errors") or []
        
        tool_execution_result = None
        if tool_status:
            success_msg = None
            resource_id = None
            if isinstance(tool_result, dict):
                success_msg = tool_result.get("message")
                resource_id = ConversationResponseMapper._stringify_optional(
                    tool_result.get("id") or tool_result.get("created_id")
                )
            elif tool_result:
                success_msg = str(tool_result)

            tool_execution_result = ToolExecutionResult(
                status=tool_status,
                created_resource_id=resource_id,
                success_message=success_msg,
                validation_warnings=validation_errors
            )

        # Conversation Status is centrally managed in the state now
        conversation_status = final_state.get("conversation_status", ConversationStatus.COLLECTING_INFORMATION)

        # Conversation Metadata
        metadata = final_state.get("metadata", {})
        conversation_metadata = None
        if metadata:
            conversation_metadata = ConversationMetadata(**metadata)
        else:
            conversation_metadata = ConversationMetadata()

        llm_response = final_state.get("llm_response")
        if not isinstance(llm_response, str) or not llm_response.strip():
            # If there's an empty response but validation errors occurred, surface them
            if validation_errors:
                llm_response = f"Backend Error: {', '.join(validation_errors)}"
            else:
                from app.services.fallback_templates import fallback_templates
                llm_response = fallback_templates.generate_fallback_response(final_state)

        return ConversationResponse(
            assistant_message=llm_response,
            conversation_id=final_state.get("conversation_id", ""),
            interaction_draft=draft,
            draft_status=draft_status, # DraftStatus is a string/enum, might need coercion if it's stored differently
            draft_changes=field_changes,
            clarification_state=final_state.get("clarification_state"),
            decision_output=final_state.get("decision_output"),
            tool_execution_result=tool_execution_result,
            conversation_status=conversation_status,
            conversation_metadata=conversation_metadata
        )
