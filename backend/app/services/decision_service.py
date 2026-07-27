import json
from typing import Dict, Any
from app.graph.state import GraphState
from app.llm.factory import get_llm_provider
from app.prompts.loader import load_prompt
from app.schemas.decision import DecisionOutput
from app.schemas.draft import ComplaintDraft
from app.shared.enums import AgentAction
from app.services.context_builder import context_builder
from app.core.config import settings
from loguru import logger

class AgentDecisionService:
    """Service to handle agent orchestration and decision making."""

    def _normalize_message(self, message: str) -> str:
        return (message or "").strip().lower().rstrip(".!?")

    def _is_confirmation(self, message: str) -> bool:
        normalized = self._normalize_message(message)
        confirmations = {
            "ok",
            "okay",
            "yes",
            "y",
            "confirm",
            "confirmed",
            "go ahead",
            "execute",
            "save",
            "save complaint",
            "log it",
            "yes execute",
            "yes, execute",
            "yes save",
            "yes, save",
        }
        return normalized in confirmations

    def _is_new_interaction_request(self, message: str) -> bool:
        normalized = self._normalize_message(message)
        explicit_phrases = [
            "another complaint",
            "new complaint",
            "log another",
            "log a new",
            "start another",
            "start a new",
            "create another",
            "create a new",
            "i want to log another",
            "i want to create another",
        ]
        return any(phrase in normalized for phrase in explicit_phrases)

    def _is_yes_to_new_interaction_prompt(self, message: str, metadata: Dict[str, Any]) -> bool:
        normalized = self._normalize_message(message)
        return bool(metadata.get("awaiting_new_complaint_decision")) and normalized in {
            "yes",
            "y",
            "yeah",
            "yep",
            "sure",
        }
    
    async def determine_next_action(self, state: GraphState) -> DecisionOutput:
        logger.info(f"[{state.get('request_id')}] AgentDecisionService: Determining next action")
        
        llm = get_llm_provider()
        decision_prompt_template = load_prompt("decision.md")
        
        # Prepare context for the prompt
        intent = state.get("detected_intent", "Unknown")
        current_draft = state.get("complaint_draft")
        if not current_draft:
            current_draft = ComplaintDraft()
            
        from app.services.draft_service import DraftService
        draft_service = DraftService()
        logger.info(f"DEBUG: detected_intent in state: {state.get('detected_intent')}")
        
        current_agent_state = state.get("current_agent_state", "IDLE")
        pending_tool = state.get("pending_tool")
        selected_tool = state.get("selected_tool")
        
        # Ensure we extract the string value if it's an Enum
        if hasattr(pending_tool, "value"):
            pending_tool = pending_tool.value
        if hasattr(selected_tool, "value"):
            selected_tool = selected_tool.value
        metadata = state.get("metadata", {})
        user_message = state.get("user_message", "")
            
        from app.tools.registry import tool_registry
        from app.shared.enums import ClarificationLifecycle

        clarification = state.get("clarification_state")
        clarification_active = bool(
            clarification and clarification.status in [
                ClarificationLifecycle.CREATED,
                ClarificationLifecycle.ACTIVE,
                ClarificationLifecycle.UPDATED,
            ]
        )

        # Outside an active clarification, a fresh explicit tool intent should not inherit
        # a stale pending_tool from a previously completed workflow.
        if not clarification_active and tool_registry.get_tool(str(intent)):
            pending_tool_name = intent
        else:
            pending_tool_name = pending_tool or selected_tool or intent

        tool = tool_registry.get_tool(pending_tool_name)
        if tool:
            required_fields = tool.get_required_fields()
            optional_fields = tool.get_optional_fields()
        else:
            required_fields = draft_service.REQUIRED_FIELDS
            optional_fields = draft_service.OPTIONAL_FIELDS
            
        # Initial validation (will be re-evaluated if context resets)
        validation_info = draft_service.validate_against_schema(current_draft, required_fields, optional_fields)
        
        draft_status = validation_info["status"].value
        required_missing = validation_info["required_missing"]
        optional_missing = validation_info["optional_missing"]
        
        prompt_required_missing = required_missing
        
        # We need to serialize the draft properly
        draft_json = current_draft.model_dump_json(indent=2)
        
        # Use context builder for the rest of the context
        builder_context = await context_builder.build(state)
        
        context_str = (
            f"Detected Intent: {intent}\n"
            f"Current Agent State: {current_agent_state}\n"
            f"Draft Status: {draft_status}\n"
            f"Required Missing Fields (Deterministic): {prompt_required_missing}\n"
            f"Pending Tool: {pending_tool_name}\n"
            f"\n{builder_context}"
        )

        if settings.DEMO_OFFLINE_MODE or metadata.get("llm_unavailable"):
            from app.shared.enums import ToolReadiness, AgentState, ToolName

            is_tool_intent = tool_registry.get_tool(str(pending_tool_name)) is not None if pending_tool_name else False
            selected_tool = None
            if is_tool_intent:
                try:
                    selected_tool = ToolName(str(pending_tool_name))
                except ValueError:
                    selected_tool = None

            if not is_tool_intent or intent in ["conversation", "unknown", "Unknown"]:
                action = AgentAction.RESPOND
                tool_readiness = ToolReadiness.NOT_APPLICABLE
                next_state = AgentState.IDLE
            elif validation_info["is_ready"]:
                tool_readiness = ToolReadiness.READY
                next_state = AgentState.READY_TO_EXECUTE
                action = AgentAction.EXECUTE_TOOL if self._is_confirmation(user_message) else AgentAction.CONTINUE
            else:
                action = AgentAction.CLARIFY
                tool_readiness = ToolReadiness.NOT_READY
                next_state = AgentState.WAITING_FOR_USER

            return DecisionOutput(
                action=action,
                tool_readiness=tool_readiness,
                selected_tool=selected_tool,
                clarification_message=None,
                clarification_reason=None,
                required_missing_fields=required_missing,
                optional_missing_fields=optional_missing,
                decision_confidence=0.7,
                next_state=next_state,
                reset_context=False,
            )
        
        messages = [
            {"role": "system", "content": decision_prompt_template},
            {"role": "system", "content": "CURRENT CONTEXT:\n" + context_str},
            {"role": "user", "content": state["user_message"]}
        ]
        
        try:
            output: DecisionOutput = await llm.generate_structured(messages=messages, schema=DecisionOutput)
            
            from app.shared.enums import ToolReadiness, AgentState
            from app.exceptions.base import WorkflowInvariantError
            
            reset_context = False
            use_latest_extracted_for_reset = True
            
            # Check for Intent Pivot during active clarification
            if clarification_active:
                if intent not in ["conversation", "Unknown", pending_tool_name]:
                    intent_confidence = state.get("metadata", {}).get("intent_confidence", 0.0)
                    if intent_confidence > 0.7:
                        logger.info(f"[{state.get('request_id')}] DecisionService: Explicit Intent Pivot detected from {pending_tool_name} to {intent}")
                        reset_context = True
                        pending_tool_name = intent
                        
            # Check if starting a completely new complaint after previous completion
            if state.get("conversation_status") == "COMPLETED" or getattr(state.get("conversation_status"), "value", None) == "COMPLETED":
                if intent == "save_complaint":
                    if self._is_new_interaction_request(user_message) or self._is_yes_to_new_interaction_prompt(user_message, metadata):
                        logger.info(f"[{state.get('request_id')}] DecisionService: Starting new {intent} workflow, requesting context reset.")
                        reset_context = True
                        pending_tool_name = intent
                    else:
                        logger.info(f"[{state.get('request_id')}] DecisionService: Ignoring non-explicit new complaint shift; keeping active complaint context.")
                        if metadata.get("active_complaint_id"):
                            pending_tool_name = "edit_complaint"
                elif intent == "edit_complaint":
                    logger.info(f"[{state.get('request_id')}] DecisionService: Editing the active completed complaint.")
                    pending_tool_name = intent
                elif intent in ["conversation", "unknown", "Unknown"] and self._is_yes_to_new_interaction_prompt(user_message, metadata):
                    logger.info(f"[{state.get('request_id')}] DecisionService: User accepted prompt to start another complaint.")
                    reset_context = True
                    pending_tool_name = "save_complaint"
                    use_latest_extracted_for_reset = False
                    
            if reset_context and pending_tool_name:
                intent = pending_tool_name

            tool = tool_registry.get_tool(pending_tool_name)
            if tool:
                required_fields = tool.get_required_fields()
                optional_fields = tool.get_optional_fields()
            else:
                required_fields = draft_service.REQUIRED_FIELDS
                optional_fields = draft_service.OPTIONAL_FIELDS
            validation_info = draft_service.validate_against_schema(current_draft, required_fields, optional_fields)

            if reset_context:
                # Re-evaluate validation on what will be the fresh draft
                latest_extracted = state.get("metadata", {}).get("latest_extracted_fields", {}) if use_latest_extracted_for_reset else {}
                fresh_draft = draft_service.merge(ComplaintDraft(), latest_extracted).updated_draft
                validation_info = draft_service.validate_against_schema(fresh_draft, required_fields, optional_fields)
            
            draft_status = validation_info["status"].value
            required_missing = validation_info["required_missing"]
            optional_missing = validation_info["optional_missing"]
            
            from app.shared.enums import ToolReadiness, AgentState, ToolName
            from app.exceptions.base import WorkflowInvariantError
            
            # Deterministic workflow logic: LLM does not dictate action, tool_readiness, or next_state
            # Only apply this strictly if we are actively dealing with a tool
            is_tool_intent = tool_registry.get_tool(str(pending_tool_name)) is not None if pending_tool_name else False
            selected_tool = None
            if is_tool_intent:
                try:
                    selected_tool = ToolName(str(pending_tool_name))
                except ValueError:
                    selected_tool = output.selected_tool
            
            is_confirmation = self._is_confirmation(state.get("user_message", ""))

            if (
                intent in ["conversation", "cancel", "unknown"]
                and not (is_confirmation and is_tool_intent and validation_info["is_ready"])
            ) or not intent or not is_tool_intent:
                action = output.action if output.action in [AgentAction.RESPOND] else AgentAction.RESPOND
                tool_readiness = ToolReadiness.NOT_APPLICABLE
                next_state = AgentState.IDLE
            else:
                if validation_info["is_ready"]:
                    tool_readiness = ToolReadiness.READY
                    next_state = AgentState.READY_TO_EXECUTE
                    if (
                        str(pending_tool_name) == "edit_complaint"
                        and state.get("changed_fields")
                    ):
                        action = AgentAction.EXECUTE_TOOL
                    elif is_confirmation or output.action == AgentAction.EXECUTE_TOOL:
                        action = AgentAction.EXECUTE_TOOL
                    else:
                        action = AgentAction.CONTINUE
                else:
                    action = AgentAction.CLARIFY
                    tool_readiness = ToolReadiness.NOT_READY
                    next_state = AgentState.WAITING_FOR_USER
                    
            # Invariant checks
            if action == AgentAction.EXECUTE_TOOL and tool_readiness != ToolReadiness.READY:
                raise WorkflowInvariantError("EXECUTE_TOOL action requested but tool is NOT_READY")
            if action == AgentAction.CLARIFY and tool_readiness == ToolReadiness.READY:
                raise WorkflowInvariantError("CLARIFY action requested but tool is already READY")
            if action == AgentAction.EXECUTE_TOOL and next_state != AgentState.READY_TO_EXECUTE:
                raise WorkflowInvariantError("EXECUTE_TOOL must imply READY_TO_EXECUTE next state")
            if action == AgentAction.CLARIFY and next_state != AgentState.WAITING_FOR_USER:
                raise WorkflowInvariantError("CLARIFY must imply WAITING_FOR_USER next state")
            if action == AgentAction.RESPOND and next_state != AgentState.IDLE:
                raise WorkflowInvariantError("RESPOND must imply IDLE next state")
                
            output = output.model_copy(update={
                "required_missing_fields": required_missing,
                "optional_missing_fields": optional_missing,
                "tool_readiness": tool_readiness,
                "action": action,
                "next_state": next_state,
                "selected_tool": selected_tool,
                "reset_context": reset_context
            })
                
            logger.info(f"[{state.get('request_id')}] DecisionEngine Output: action={output.action}, next_state={output.next_state}, readiness={output.tool_readiness}")
            return output
        except Exception as e:
            logger.error(f"[{state.get('request_id')}] AgentDecisionService Error: {e}")
            from app.shared.enums import ToolReadiness, AgentState
            # Fallback using deterministic rules instead of blind RESPOND
            # We already know validation_info!
            if intent == "conversation" or not intent:
                action = AgentAction.RESPOND
                tool_readiness = ToolReadiness.NOT_APPLICABLE
                next_state = AgentState.IDLE
            else:
                if validation_info["is_ready"]:
                    action = AgentAction.EXECUTE_TOOL if self._is_confirmation(state.get("user_message", "")) else AgentAction.CONTINUE
                    tool_readiness = ToolReadiness.READY
                    next_state = AgentState.READY_TO_EXECUTE
                else:
                    action = AgentAction.CLARIFY
                    tool_readiness = ToolReadiness.NOT_READY
                    next_state = AgentState.WAITING_FOR_USER
                    
            from app.shared.enums import ToolName
            
            valid_tool = None
            try:
                valid_tool = ToolName(pending_tool_name) if pending_tool_name else None
            except ValueError:
                pass
            
            return DecisionOutput(
                action=action,
                tool_readiness=tool_readiness,
                selected_tool=valid_tool,
                clarification_message=None,
                clarification_reason=None,
                required_missing_fields=required_missing,
                optional_missing_fields=optional_missing,
                decision_confidence=0.0,
                next_state=next_state,
                reset_context=False
            )

decision_service = AgentDecisionService()
