from typing import Dict, Any, List
from app.graph.state import GraphState
from app.services.conversation_memory import conversation_memory_service
from app.schemas.draft import InteractionDraft
from app.schemas.memory import ClarificationState, ConversationSummary
import json
from datetime import date

class ContextBuilder:
    """
    Responsible for assembling structured context for LLM prompts.
    Does NOT contain prompt templates (those belong in PromptLoader).
    Produces context blocks that can be appended to or injected into templates.
    """
    
    @classmethod
    async def build(cls, state: GraphState, exclude_history: bool = False) -> str:
        """
        Builds a comprehensive structured context string using memory and current state.
        If exclude_history is True, omits overall summary and past messages.
        """
        conversation_id = state.get("conversation_id", "default")
        
        # Gather data from memory service
        summary = await conversation_memory_service.get_summary(conversation_id)
        
        # Get metadata to determine interaction boundaries
        metadata = await conversation_memory_service.get_metadata(conversation_id)
        state_metadata = state.get("metadata", {})
        start_idx = state_metadata.get("current_interaction_start_idx", 0)
        
        # Calculate how many messages belong to the current interaction
        current_message_count = metadata.message_count
        messages_in_current_interaction = max(0, current_message_count - start_idx)
        
        # We always fetch a baseline limit, but if excluding history, we slice it
        fetch_limit = messages_in_current_interaction if exclude_history and messages_in_current_interaction > 0 else 5
        # Fallback to at least fetching something if the math is 0, but slice logic will handle it
        recent_messages = await conversation_memory_service.get_recent_messages(conversation_id, limit=max(5, fetch_limit))
        
        if exclude_history and messages_in_current_interaction > 0:
            recent_messages = recent_messages[-messages_in_current_interaction:]
        elif exclude_history and messages_in_current_interaction == 0:
            recent_messages = []
            
        resolved_entities = await conversation_memory_service.repo.get_resolved_entities(conversation_id)
        
        # Gather data from current GraphState
        draft = state.get("interaction_draft")
        clarification = state.get("clarification_state")
        tool_result = state.get("tool_result")
        validation_errors = state.get("validation_errors")

        context_blocks = []

        context_blocks.append(f"### Current Date\n{date.today().isoformat()}")

        if not exclude_history and summary:
            context_blocks.append(cls._format_summary(summary))
            
        if not exclude_history and metadata:
            context_blocks.append(cls._format_metadata(metadata))

        if resolved_entities:
            context_blocks.append(f"### Resolved Entities\n```json\n{json.dumps(resolved_entities, indent=2)}\n```")

        if draft:
            context_blocks.append(cls._format_draft(draft))

        from app.shared.enums import ClarificationLifecycle
        if clarification and clarification.status in [ClarificationLifecycle.CREATED, ClarificationLifecycle.ACTIVE, ClarificationLifecycle.UPDATED]:
            context_blocks.append(cls._format_clarification(clarification))
            
        decision_output = state.get("decision_output")
        if decision_output:
            context_blocks.append(f"### Decision Output\n```json\n{decision_output.model_dump_json(indent=2)}\n```")
            
        conversation_status = state.get("conversation_status")
        if conversation_status:
            context_blocks.append(f"### Conversation Status\n{conversation_status.value}")
            
        current_agent_state = state.get("current_agent_state")
        if current_agent_state:
            context_blocks.append(f"### Current Agent State\n{current_agent_state.value if hasattr(current_agent_state, 'value') else current_agent_state}")
            
        selected_tool = state.get("selected_tool")
        if selected_tool:
            context_blocks.append(f"### Selected Tool\n{selected_tool}")

        if tool_result:
            context_blocks.append(f"### Previous Tool Result\n```json\n{json.dumps(tool_result, indent=2, default=str)}\n```")
        elif validation_errors:
            context_blocks.append(f"### Previous Tool Execution Failed\n```json\n{json.dumps(validation_errors, indent=2)}\n```")

        if recent_messages:
            context_blocks.append(cls._format_recent_messages(recent_messages))

        return "\n\n".join(context_blocks)

    @staticmethod
    def _format_summary(summary: ConversationSummary) -> str:
        return f"### Conversation Summary\n```json\n{summary.model_dump_json(indent=2)}\n```"
        
    @staticmethod
    def _format_metadata(metadata: Any) -> str:
        # metadata is ConversationMetadata
        return f"### Conversation Metadata\n```json\n{metadata.model_dump_json(indent=2)}\n```"

    @staticmethod
    def _format_draft(draft: InteractionDraft) -> str:
        return f"### Current Interaction Draft\n```json\n{draft.model_dump_json(indent=2)}\n```"

    @staticmethod
    def _format_clarification(clarification: ClarificationState) -> str:
        return f"### Active Clarification State\n```json\n{clarification.model_dump_json(indent=2)}\n```"

    @staticmethod
    def _format_recent_messages(messages: List[Any]) -> str:
        formatted = "### Recent Conversation History\n"
        for m in messages:
            formatted += f"**{m.role}**: {m.content}\n"
        return formatted

context_builder = ContextBuilder()
