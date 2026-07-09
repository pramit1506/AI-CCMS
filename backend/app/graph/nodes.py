import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from app.graph.state import GraphState, IntentOutput, ToolSelectionOutput
from app.llm.factory import get_llm_provider
from app.prompts.loader import load_prompt
from app.tools.registry import tool_registry
from app.tools.context import ToolExecutionContext
from app.schemas.extraction import ExtractionOutput
from app.services.draft_service import DraftService
from app.schemas.draft import FieldMetadata, InteractionDraft
from app.services.decision_service import decision_service
from app.services.context_builder import context_builder
from app.services.conversation_memory import conversation_memory_service
from app.services.fallback_templates import fallback_templates
from app.exceptions.base import ProviderException, RateLimitException, TimeoutException, InvalidAPIKeyException, ModelUnavailableException
from app.shared.enums import AgentAction
from loguru import logger

async def input_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Input Node: Received message for conversation {state.get('conversation_id')}")
    # Persist the incoming user message
    if state.get("conversation_id") and state.get("user_message"):
        await conversation_memory_service.append_message(
            state["conversation_id"], 
            "user", 
            state["user_message"]
        )
        
    # The DecisionService determines if a new interaction starts (and sets reset_context=True).
    # Here, we only clear transient execution artifacts so they don't linger.
    updates = {
        "tool_result": None,
        "tool_status": None,
        "validation_errors": None
    }
        
    return updates

async def intent_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Intent Node: Detecting intent")

    from app.shared.enums import ClarificationLifecycle

    clarification = state.get("clarification_state")
    if clarification and clarification.status in [
        ClarificationLifecycle.CREATED,
        ClarificationLifecycle.ACTIVE,
        ClarificationLifecycle.UPDATED,
    ]:
        normalized_message = state.get("user_message", "").strip().lower().rstrip(".!?")
        cancel_like = normalized_message in {
            "cancel",
            "cancel that",
            "cancel it",
            "stop",
            "nevermind",
            "never mind",
        }
        if not cancel_like:
            tool_name = clarification.tool_name or state.get("pending_tool") or state.get("selected_tool")
            logger.info(
                f"[{state.get('request_id')}] Intent Node: Active clarification for {tool_name}; preserving workflow intent"
            )
            return {"detected_intent": tool_name}
    
    # We always detect intent to allow for pivoting. DecisionService will determine if a pivot should occur.
    llm = get_llm_provider()
    system_prompt = load_prompt("system.md")
    intent_prompt = load_prompt("intent.md")
    
    context_str = await context_builder.build(state)
    
    messages = [
        {"role": "system", "content": system_prompt + "\n\n" + context_str},
        {"role": "system", "content": intent_prompt},
        {"role": "user", "content": state["user_message"]}
    ]
    
    try:
        intent_output = await llm.generate_structured(messages=messages, schema=IntentOutput)
        logger.info(f"[{state.get('request_id')}] Intent detected: {intent_output.intent}")
        metadata = state.get("metadata", {}).copy()
        metadata["intent_confidence"] = intent_output.confidence
        return {"detected_intent": intent_output.intent, "metadata": metadata}
    except Exception as e:
        logger.error(f"[{state.get('request_id')}] Intent Node Error: {e}")
        return {"detected_intent": "conversation"}

def normalize_extracted_fields(fields_dict: Dict[str, Any]) -> None:
    if not fields_dict: return
    if "status" in fields_dict and isinstance(fields_dict["status"], str):
        val = fields_dict["status"].upper().strip()
        if "COMPLET" in val: fields_dict["status"] = "COMPLETED"
        elif "PLAN" in val: fields_dict["status"] = "PLANNED"
        elif "CANCEL" in val: fields_dict["status"] = "CANCELLED"
        elif "SHOW" in val: fields_dict["status"] = "NO_SHOW"
        else: fields_dict["status"] = val.replace(" ", "_")
    if "interaction_type" in fields_dict and isinstance(fields_dict["interaction_type"], str):
        val = fields_dict["interaction_type"].upper().strip()
        if "EMAIL" in val: fields_dict["interaction_type"] = "EMAIL"
        elif "PERSON" in val: fields_dict["interaction_type"] = "IN_PERSON"
        elif "VIRTUAL" in val or "VIDEO" in val: fields_dict["interaction_type"] = "VIRTUAL"
        elif "PHONE" in val or "CALL" in val: fields_dict["interaction_type"] = "PHONE"
        else: fields_dict["interaction_type"] = val.replace(" ", "_")


async def entity_extraction_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Entity Extraction Node: Extracting entities")
    
    intent = state.get("detected_intent")
    if intent == "conversation":
        logger.info(f"[{state.get('request_id')}] Skipping extraction for conversation intent")
        return {}
        
    llm = get_llm_provider()
    extraction_prompt = load_prompt("entity_extraction.md")
    
    current_draft = state.get("interaction_draft")
    if not current_draft:
        current_draft = InteractionDraft()
        
    # Build context using context_builder which includes draft, and resolved entities
    # Exclude history to prevent contamination from past interactions
    context_str = await context_builder.build(state, exclude_history=True)
    
    messages = [
        {"role": "system", "content": extraction_prompt + "\n\n" + context_str},
        {"role": "user", "content": state["user_message"]}
    ]
    
    try:
        output: ExtractionOutput = await llm.generate_structured(messages=messages, schema=ExtractionOutput)
        logger.info(f"[{state.get('request_id')}] Extraction output: {output.model_dump()}")
        
        draft_service = DraftService()
        draft = current_draft
        all_changed_fields = []
        
        # 1. Merge extracted fields
        if output.extracted_fields:
            normalize_extracted_fields(output.extracted_fields)
            metadata_dict = {}
            for field, meta in output.field_metadata.items():
                if field in output.extracted_fields:
                    metadata_dict[field] = FieldMetadata(**meta)
            
            result = draft_service.merge(draft, output.extracted_fields, metadata=metadata_dict)
            draft = result.updated_draft
            all_changed_fields.extend(result.changed_fields)
            
        # 2. Apply corrections
        if output.corrections:
            normalize_extracted_fields(output.corrections)
            for field, new_value in output.corrections.items():
                meta = output.field_metadata.get(field)
                meta_obj = FieldMetadata(**meta) if meta else None
                result = draft_service.correct_field(draft, field, new_value, metadata=meta_obj)
                draft = result.updated_draft
                all_changed_fields.extend(result.changed_fields)
                
        # 3. Apply removals
        if output.removed_fields:
            for field in output.removed_fields:
                result = draft_service.remove_field(draft, field)
                draft = result.updated_draft
                all_changed_fields.extend(result.changed_fields)
                
        # Remove duplicates from changed fields
        all_changed_fields = list(set(all_changed_fields))
        
        status_info = draft_service.validate(draft)
        draft_status = status_info["status"].value
        
        metadata = state.get("metadata", {}).copy()
        # Save raw extracted fields for decision_node in case of context reset
        metadata["latest_extracted_fields"] = output.extracted_fields
        metadata["latest_field_metadata"] = output.field_metadata
        
        return {
            "interaction_draft": draft,
            "changed_fields": all_changed_fields,
            "draft_status": draft_status,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"[{state.get('request_id')}] Entity Extraction Error: {e}")
        return {}

async def decision_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Decision Node: Planning next step")
    
    decision_output = await decision_service.determine_next_action(state)
    
    from app.shared.enums import ConversationStatus, ClarificationLifecycle, AgentAction, ToolReadiness
    conversation_status = ConversationStatus.COLLECTING_INFORMATION
    if decision_output.action == AgentAction.CLARIFY:
        conversation_status = ConversationStatus.AWAITING_CLARIFICATION
    elif decision_output.action == AgentAction.EXECUTE_TOOL:
        conversation_status = ConversationStatus.READY_FOR_EXECUTION
        
    updates = {
        "decision_output": decision_output,
        "current_agent_state": decision_output.next_state,
        "clarification_reason": decision_output.clarification_reason,
        "required_missing_fields": decision_output.required_missing_fields,
        "optional_missing_fields": decision_output.optional_missing_fields,
        "conversation_status": conversation_status
    }
    
    metadata = state.get("metadata", {}).copy()
    normalized_message = state.get("user_message", "").strip().lower().rstrip(".!?")
    if metadata.get("awaiting_new_interaction_decision") and normalized_message in {
        "no",
        "n",
        "nope",
        "no thanks",
        "not now",
    }:
        metadata["awaiting_new_interaction_decision"] = False
    
    if hasattr(decision_output, "reset_context") and decision_output.reset_context:
        logger.info(f"[{state.get('request_id')}] Decision Node: Executing state reset for new workflow/pivot.")
        metadata["current_interaction_start_idx"] = metadata.get("message_count", 0)
        metadata["awaiting_new_interaction_decision"] = False
        
        # Completely clear old state
        updates["interaction_draft"] = None
        updates["clarification_state"] = None
        updates["selected_tool"] = None
        updates["pending_tool"] = None
        updates["tool_arguments"] = None
        
        # Apply fresh extraction directly to new draft
        latest_extracted = metadata.get("latest_extracted_fields")
        if latest_extracted:
            from app.services.draft_service import DraftService
            draft_service = DraftService()
            fresh_draft = InteractionDraft()
            
            latest_meta = metadata.get("latest_field_metadata", {})
            meta_dict = {}
            for field, m in latest_meta.items():
                if field in latest_extracted:
                    meta_dict[field] = FieldMetadata(**m)
                    
            fresh_draft = draft_service.merge(fresh_draft, latest_extracted, metadata=meta_dict).updated_draft
            updates["interaction_draft"] = fresh_draft
            
    updates["metadata"] = metadata
    
    if decision_output.selected_tool:
        updates["selected_tool"] = decision_output.selected_tool
        updates["pending_tool"] = decision_output.selected_tool
        
    clarification = state.get("clarification_state")
    if decision_output.action == AgentAction.CLARIFY:
        from app.schemas.memory import ClarificationState
        if not clarification:
            clarification = ClarificationState(
                tool_name=decision_output.selected_tool or "unknown",
                required_fields=decision_output.required_missing_fields,
                missing_fields=decision_output.required_missing_fields,
                original_request=state.get("user_message", ""),
                status=ClarificationLifecycle.CREATED
            )
        else:
            clarification.missing_fields = decision_output.required_missing_fields
            clarification.status = ClarificationLifecycle.UPDATED
        updates["clarification_state"] = clarification
    else:
        if clarification and decision_output.tool_readiness == ToolReadiness.READY:
            clarification.status = ClarificationLifecycle.CLEARED
            updates["clarification_state"] = None
            
    return updates

async def tool_selection_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Tool Selection Node: Selecting tool")
    
    tool_name = state.get("selected_tool")
    intent = state.get("detected_intent")
    
    if tool_name:
        tool = tool_registry.get_tool(tool_name)
    else:
        tool = tool_registry.get_tool(intent)
    
    if not tool:
        logger.warning(f"[{state.get('request_id')}] No tool found for intent {intent}")
        return {}

    decision = state.get("decision_output")
    from app.shared.enums import AgentAction
    
    if decision and decision.action == AgentAction.EXECUTE_TOOL:
        draft = state.get("interaction_draft")
        if draft:
            draft_dict = draft.model_dump(exclude_none=True)
            tool_schema_fields = tool.args_schema.model_fields.keys()
            tool_args = {k: v for k, v in draft_dict.items() if k in tool_schema_fields}
        else:
            tool_args = {}
            
        logger.info(f"[{state.get('request_id')}] Selected tool: {tool.name}")
        logger.info(f"[{state.get('request_id')}] Tool arguments mapped directly from InteractionDraft")
        
        return {
            "selected_tool": tool.name,
            "tool_arguments": tool_args
        }

    llm = get_llm_provider()
    tool_selection_prompt = load_prompt("tool_selection.md").format(
        tool_name=tool.name,
        tool_description=tool.description
    )
    
    schema_json = json.dumps(tool.args_schema.model_json_schema())
    tool_selection_prompt += f"\n\nArguments Schema: {schema_json}"
    tool_selection_prompt += "\n\nIMPORTANT: Place the extracted arguments directly into the `tool_arguments` field of your JSON response."
    
    context_str = await context_builder.build(state)
    
    messages = [
        {"role": "system", "content": tool_selection_prompt + "\n\n" + context_str},
        {"role": "user", "content": state["user_message"]}
    ]
    
    try:
        output = await llm.generate_structured(messages=messages, schema=ToolSelectionOutput)
        logger.info(f"[{state.get('request_id')}] Selected tool: {tool.name}")
        logger.info(f"[{state.get('request_id')}] Tool arguments: {output.tool_arguments}")
        
        return {
            "selected_tool": tool.name,
            "tool_arguments": output.tool_arguments
        }
    except Exception as e:
        logger.error(f"[{state.get('request_id')}] Tool Selection Error: {e}")
        from app.shared.enums import ConversationStatus
        return {
            "tool_arguments": {},
            "tool_status": "failed",
            "validation_errors": [f"Tool selection failed: {str(e)}"],
            "conversation_status": ConversationStatus.COLLECTING_INFORMATION
        }

async def tool_execution_node(state: GraphState, config: RunnableConfig) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Tool Execution Node: Executing {state.get('selected_tool')}")
    
    decision = state.get("decision_output")
    from app.shared.enums import ToolReadiness, ConversationStatus, DraftStatus
    if not decision or decision.tool_readiness != ToolReadiness.READY:
        logger.error(f"[{state.get('request_id')}] Workflow Invariant Violation: Tool execution attempted while NOT_READY")
        raise RuntimeError("Workflow Invariant Violation: Tool execution attempted while NOT_READY")
        
    draft = state.get("interaction_draft")
    if not draft:
        logger.error(f"[{state.get('request_id')}] Workflow Invariant Violation: Tool execution attempted with no InteractionDraft")
        return {"tool_status": "failed", "validation_errors": ["No InteractionDraft found."]}
        
    tool_name = state.get("selected_tool")
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        return {"tool_status": "failed", "validation_errors": ["Tool not found."]}
    tool_name_value = tool_name.value if hasattr(tool_name, "value") else str(tool_name)

    draft_service = DraftService()
    required_fields = tool.get_required_fields()
    optional_fields = tool.get_optional_fields()
    
    status_info = draft_service.validate_against_schema(draft, required_fields, optional_fields)
    
    if status_info["status"] != DraftStatus.READY:
        logger.warning(f"[{state.get('request_id')}] Tool Execution Node: Draft is not READY, rejecting execution.")
        return {
            "tool_status": "failed",
            "validation_errors": [f"Draft is missing required fields: {status_info.get('required_missing', [])}"],
            # Do NOT compute a new workflow transition, just return the validation failure.
        }
    
    tool_args = state.get("tool_arguments") or {}

    if tool_name_value == "edit_interaction" and not tool_args.get("id"):
        active_interaction_id = (state.get("metadata") or {}).get("active_interaction_id")
        if not active_interaction_id:
            logger.warning(f"[{state.get('request_id')}] EditInteraction requested without an active interaction id.")
            return {
                "tool_status": "failed",
                "validation_errors": ["No active interaction is available to edit."],
                "conversation_status": ConversationStatus.COLLECTING_INFORMATION,
            }
        tool_args = {**tool_args, "id": active_interaction_id}
    
    logger.info(f"[{state.get('request_id')}] Executing tool: {tool_name}")
        
    context: ToolExecutionContext = config["configurable"].get("tool_context")
    if not context:
        logger.error("ToolExecutionContext not found in config")
        return {"tool_status": "failed", "validation_errors": ["Execution context missing."]}
        
    try:
        validated_args = tool.args_schema(**tool_args)
        logger.info(f"[{state.get('request_id')}] Validated arguments: {validated_args.model_dump()}")
        
        result = await tool.execute(context, **validated_args.model_dump())
        logger.info(f"[{state.get('request_id')}] Tool execution result: {result}")

        result_status = None
        if isinstance(result, dict):
            result_status = str(result.get("status", "")).lower()

        if result_status in {"failed", "failure", "error"}:
            message = result.get("message") or "Tool execution failed."
            error_state = {
                "tool_result": result,
                "tool_status": "failed",
                "validation_errors": [message],
                "conversation_status": ConversationStatus.COLLECTING_INFORMATION,
            }
            logger.info(f"[{state.get('request_id')}] GraphState after execution: {error_state}")
            return error_state
        
        from app.shared.enums import ConversationStatus
        metadata = state.get("metadata", {}).copy()
        if isinstance(result, dict):
            if result.get("id"):
                metadata["active_interaction_id"] = str(result.get("id"))
            if result.get("interaction_number"):
                metadata["active_interaction"] = result.get("interaction_number")
            metadata["last_tool"] = tool_name_value
            if tool_name_value == "log_interaction":
                metadata["awaiting_new_interaction_decision"] = True

        new_state = {
            "tool_result": result,
            "tool_status": "success",
            "validation_errors": [],
            "conversation_status": ConversationStatus.COMPLETED,
            "metadata": metadata
        }
        logger.info(f"[{state.get('request_id')}] GraphState after execution: {new_state}")
        return new_state
        
    except Exception as e:
        logger.error(f"[{state.get('request_id')}] Tool Execution Error: {e}")
        from app.shared.enums import ConversationStatus
        error_state = {
            "tool_status": "failed",
            "validation_errors": [str(e)],
            "conversation_status": ConversationStatus.COLLECTING_INFORMATION
        }
        logger.info(f"[{state.get('request_id')}] GraphState after execution: {error_state}")
        return error_state

async def response_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Response Node: Generating response")
    # Response Node is strictly presentation-only.
    # It must NEVER modify workflow state, DecisionOutput, or ConversationStatus.
    llm = get_llm_provider()
    
    decision = state.get("decision_output")
    context_str = await context_builder.build(state)
    
    messages = []
    
    if decision and decision.action == AgentAction.CLARIFY:
        clarification_message = decision.clarification_message or "I need more information to proceed."
        clarification_prompt = load_prompt("clarification.md").format(
            tool_name=state.get("selected_tool"),
            clarification_message=clarification_message
        )
        messages = [
            {"role": "system", "content": clarification_prompt + "\n\n" + context_str},
            {"role": "user", "content": state["user_message"]}
        ]
    else:
        tool_result = state.get("tool_result")
        tool_status = state.get("tool_status")
        validation_errors = state.get("validation_errors")
        
        system_prompt = load_prompt("system.md")
        response_prompt = load_prompt("response.md").format(user_message=state["user_message"])
        
        if tool_result:
            response_prompt += f"\n\nTool Result ({tool_status}):\n{json.dumps(tool_result, indent=2, default=str)}"
        elif validation_errors:
            response_prompt += f"\n\nTool Execution Failed with validation errors:\n{json.dumps(validation_errors)}"
            
        messages = [
            {"role": "system", "content": system_prompt + "\n\n" + context_str},
            {"role": "user", "content": response_prompt}
        ]
        
    try:
        response = await llm.generate_response(messages=messages)
    except ProviderException as e:
        # Transient provider failures
        logger.warning(f"[{state.get('request_id')}] Response Node: Transient provider error ({type(e).__name__}): {e}. Using deterministic fallback.")
        response = fallback_templates.generate_fallback_response(state)
    except (InvalidAPIKeyException, ModelUnavailableException) as e:
        # Permanent configuration failures
        logger.error(f"[{state.get('request_id')}] Response Node: Permanent provider configuration error ({type(e).__name__}): {e}.")
        response = "I'm currently unable to process your request because the AI service is unavailable or incorrectly configured. Please contact support."
    # Unknown exceptions are intentionally NOT caught here, allowing them to propagate up for observability
        
    # Save response to memory
    if state.get("conversation_id"):
        await conversation_memory_service.append_message(state["conversation_id"], "assistant", response)
        
    return {"llm_response": response}

async def output_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Output Node: Finalizing response")
    return {}
