import json
import re
from typing import Dict, Any
from datetime import date, timedelta
from langchain_core.runnables import RunnableConfig
from app.graph.state import GraphState, IntentOutput, ToolSelectionOutput
from app.llm.factory import get_llm_provider
from app.prompts.loader import load_prompt
from app.tools.registry import tool_registry
from app.tools.context import ToolExecutionContext
from app.schemas.extraction import ExtractionOutput
from app.services.draft_service import DraftService
from app.schemas.draft import FieldMetadata, ComplaintDraft
from app.services.decision_service import decision_service
from app.services.context_builder import context_builder
from app.services.conversation_memory import conversation_memory_service
from app.services.fallback_templates import fallback_templates
from app.exceptions.base import ProviderException, RateLimitException, TimeoutException, InvalidAPIKeyException, ModelUnavailableException
from app.shared.enums import AgentAction
from app.core.config import settings
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
        
    # The DecisionService determines if a new complaint starts (and sets reset_context=True).
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

    if settings.DEMO_OFFLINE_MODE:
        metadata = state.get("metadata", {}).copy()
        metadata["llm_unavailable"] = True
        return {"detected_intent": _fallback_intent(state.get("user_message", "")), "metadata": metadata}
    
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
        metadata = state.get("metadata", {}).copy()
        metadata["llm_unavailable"] = True
        return {"detected_intent": _fallback_intent(state.get("user_message", "")), "metadata": metadata}


def _fallback_intent(message: str) -> str:
    text = (message or "").lower()
    if any(term in text for term in ["save complaint", "log complaint", "process this uploaded document", "complaint", "batch", "lot", "product"]):
        return "save_complaint"
    if any(term in text for term in ["capa", "corrective", "preventive", "root cause"]):
        return "recommend_capa"
    if "summar" in text:
        return "summarize_complaint"
    if any(term in text for term in ["complete", "missing", "required fields"]):
        return "completeness_check"
    return "conversation"


def _parse_simple_date(value: str) -> str | None:
    text = (value or "").strip()
    today = date.today()
    lowered = text.lower()
    if "today" in lowered:
        return today.isoformat()
    if "yesterday" in lowered:
        return (today - timedelta(days=1)).isoformat()

    patterns = [
        r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b",
        r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b",
    ]
    for idx, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if not match:
            continue
        parts = [int(part) for part in match.groups()]
        try:
            if idx == 0:
                return date(parts[0], parts[1], parts[2]).isoformat()
            return date(parts[2], parts[1], parts[0]).isoformat()
        except ValueError:
            return None
    month_match = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+(\d{4})\b",
        lowered,
    )
    if month_match:
        month_names = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }
        return date(int(month_match.group(2)), month_names[month_match.group(1)], 1).isoformat()
    return None


def _first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip(" :#-\n\t")
    return None


def _is_update_message(text: str) -> bool:
    lowered = (text or "").lower()
    if "process this uploaded document" in lowered:
        return False
    update_markers = [
        "sorry",
        "actually",
        "correct",
        "correction",
        "change",
        "update",
        "replace",
        "should be",
        "batch number is",
        "affected quantity is",
        "quantity affected is",
    ]
    return any(marker in lowered for marker in update_markers)


def _fallback_extract_fields(message: str, update_mode: bool = False) -> Dict[str, Any]:
    text = message or ""
    fields: Dict[str, Any] = {}

    if "uploaded document" in text.lower() or ".pdf" in text.lower():
        fields["complaint_source"] = "PDF"
    elif "email" in text.lower() or ".eml" in text.lower():
        fields["complaint_source"] = "EMAIL"
    elif "call" in text.lower() or "phone" in text.lower():
        fields["complaint_source"] = "CALL"
    elif text.strip() and not update_mode:
        fields["complaint_source"] = "TEXT"

    customer = _first_match([
        r"^\s*([A-Z][A-Za-z0-9 &.'-]+?)\s+reported\b",
        r"(?:customer|reported by|reporter|hospital|from)\s*(?:name)?\s*[:\-]\s*([^\n,]+)",
        r"(?:customer|hospital)\s+([A-Z][A-Za-z0-9 &.'-]+)",
    ], text)
    if customer:
        fields["customer_name"] = customer

    product = _first_match([
        r"(?:product|drug|api|fdf)\s*(?:name)?\s*[:\-]\s*([^\n,]+)",
        r"\bin\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z]?[A-Za-z0-9]+){0,4}\s+API)\b",
        r"\bin\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z]?[A-Za-z0-9]+){0,4})\s+\d+(?:\.\d+)?\s*(?:mg|mcg|ml|iu|%)",
        r"\b(?:of|for)\s+([A-Z][A-Za-z]+(?:\s+[A-Z]?[A-Za-z0-9]+){0,3})\s+(?:from batch|batch|lot|\d+\s*(?:mg|ml|iu|%))",
    ], text)
    if product:
        product = re.sub(r"\s+", " ", product).strip(" .")
        fields["product_name"] = product

    strength = _first_match([
        r"(?:product\s+strength(?:/grade)?|strength/grade|grade)\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9/ .-]*?)(?=\.|,|\n|$)",
        r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|iu|%))\b",
    ], text)
    if strength:
        strength = re.sub(r"\s+", " ", strength).strip(" .")
        if re.fullmatch(r"\d+(?:\.\d+)?\s*(?:mg|mcg|ml|iu|%)", strength, flags=re.IGNORECASE):
            strength = strength.replace(" ", "")
        fields["product_strength"] = strength

    batch = _first_match([
        r"(?:batch|lot)(?:\s*(?:number|no\.?|#))?\s*(?:is|as|to|:|-)?\s*([A-Za-z0-9][A-Za-z0-9\-_/]*)",
    ], text)
    if batch:
        fields["batch_number"] = batch

    quantity = _first_match([
        r"(?:quantity affected|affected quantity|qty)\s*(?:is|as|to|:|-)?\s*([^\n.]+)",
        r"\b(\d+(?:\.\d+)?\s*(?:capsules?|kg|g|tablets?|vials?|units?|bottles?|packs?)(?:\s*\([^)]*\))?)\b",
    ], text)
    if quantity:
        fields["quantity_affected"] = quantity.strip(" .,")

    complaint_date = _first_match([
        r"(?:complaint date|received date|date received|reported on)\s*[:\-]\s*([^\n,]+)",
    ], text)
    parsed_complaint_date = _parse_simple_date(complaint_date or "")
    if parsed_complaint_date:
        fields["complaint_date"] = parsed_complaint_date
    elif not update_mode:
        fields["complaint_date"] = date.today().isoformat()

    mfg_date = _first_match([r"(?:manufacturing|mfg)\s*(?:date)?\s*[:\-]?\s*([A-Za-z]+\s+\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})"], text)
    parsed_mfg = _parse_simple_date(mfg_date or "")
    if parsed_mfg:
        fields["manufacturing_date"] = parsed_mfg

    exp_date = _first_match([r"(?:expiry|expiration|exp\.?)\s*(?:date)?\s*[:\-]?\s*([A-Za-z]+\s+\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})"], text)
    parsed_exp = _parse_simple_date(exp_date or "")
    if parsed_exp:
        fields["expiry_date"] = parsed_exp

    lowered = text.lower()
    should_update_assessment = not update_mode or any(
        term in lowered
        for term in [
            "adverse",
            "patient",
            "illness",
            "contamination",
            "foreign matter",
            "sterility",
            "discolored",
            "discolour",
            "leak",
            "broken",
            "damaged",
            "label",
            "packaging",
            "seal",
        ]
    )
    if should_update_assessment and any(term in lowered for term in ["adverse", "patient", "illness", "contamination", "foreign matter", "sterility", "discolored", "discolour"]):
        fields["complaint_type"] = "Quality"
        fields["initial_severity"] = "CRITICAL" if any(term in lowered for term in ["patient", "adverse", "sterility"]) else "MAJOR"
        fields["priority"] = "HIGH"
        fields["risk_classification"] = "High - Potential patient safety or product quality risk"
    elif should_update_assessment and any(term in lowered for term in ["leak", "broken", "damaged", "label", "packaging", "seal"]):
        fields["complaint_type"] = "Packaging"
        fields["initial_severity"] = "MINOR"
        fields["priority"] = "LOW"
        fields["risk_classification"] = "Minor - Packaging or presentation issue"
    elif not update_mode:
        fields["complaint_type"] = "Quality"
        fields["initial_severity"] = "MAJOR"
        fields["priority"] = "MEDIUM"
        fields["risk_classification"] = "Major - Quality complaint requiring QA triage"

    body = text.split("):", 1)[-1].strip() if "Process this uploaded document" in text else text.strip()
    explicit_description = re.search(r"(?:description|details?)\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    if explicit_description:
        fields["detailed_description"] = explicit_description.group(1).strip()[:2000]
    elif body and not update_mode:
        fields["detailed_description"] = body[:2000]

    if not update_mode or should_update_assessment:
        fields.setdefault("root_cause_recommendation", "Review batch manufacturing records, packaging records, and distribution handling evidence.")
        fields.setdefault("capa_recommendation", "Open QA investigation, quarantine retained samples if applicable, document findings, and define corrective/preventive actions.")
        fields.setdefault("risk_reasoning", "Risk is based on the reported complaint type, product impact, batch traceability, and potential patient or quality impact.")

    return {key: value for key, value in fields.items() if value}


def _sync_description_with_corrections(draft: ComplaintDraft, extracted_fields: Dict[str, Any]) -> None:
    if not draft or "detailed_description" in extracted_fields:
        return

    description = draft.detailed_description or ""
    if not description:
        return

    updated_description = description

    new_batch = extracted_fields.get("batch_number")
    if new_batch:
        old_batch = draft.batch_number
        if old_batch and old_batch in updated_description:
            updated_description = updated_description.replace(old_batch, str(new_batch))
        else:
            replaced = re.sub(
                r"(batch(?:\s+number)?\s*)[A-Za-z0-9\-_/]+",
                rf"\g<1>{new_batch}",
                updated_description,
                flags=re.IGNORECASE,
                count=1,
            )
            if replaced == updated_description:
                updated_description = updated_description.rstrip(". ") + f". Batch number {new_batch}."
            else:
                updated_description = replaced

    new_quantity = extracted_fields.get("quantity_affected")
    if new_quantity:
        old_quantity = draft.quantity_affected
        if old_quantity and old_quantity in updated_description:
            updated_description = updated_description.replace(old_quantity, str(new_quantity))
        else:
            replaced = re.sub(
                r"((?:affected\s+quantity|quantity\s+affected)\s*(?:is|:|-)?\s*)[^.,\n]+",
                rf"\g<1>{new_quantity}",
                updated_description,
                flags=re.IGNORECASE,
                count=1,
            )
            if replaced == updated_description:
                updated_description = updated_description.rstrip(". ") + f". Affected quantity {new_quantity}."
            else:
                updated_description = replaced

    if updated_description != description:
        extracted_fields["detailed_description"] = updated_description

def normalize_extracted_fields(fields_dict: Dict[str, Any]) -> None:
    if not fields_dict: return
    if "status" in fields_dict and isinstance(fields_dict["status"], str):
        val = fields_dict["status"].upper().strip()
        if "COMPLET" in val: fields_dict["status"] = "COMPLETED"
        elif "PLAN" in val: fields_dict["status"] = "PLANNED"
        elif "CANCEL" in val: fields_dict["status"] = "CANCELLED"
        elif "SHOW" in val: fields_dict["status"] = "NO_SHOW"
        else: fields_dict["status"] = val.replace(" ", "_")
    if "complaint_source" in fields_dict and isinstance(fields_dict["complaint_source"], str):
        val = fields_dict["complaint_source"].upper().strip()
        if "PDF" in val: fields_dict["complaint_source"] = "PDF"
        elif "EMAIL" in val or "EML" in val: fields_dict["complaint_source"] = "EMAIL"
        elif "CALL" in val or "PHONE" in val: fields_dict["complaint_source"] = "CALL"
        elif "PORTAL" in val: fields_dict["complaint_source"] = "PORTAL"
        else: fields_dict["complaint_source"] = "TEXT"
    if "initial_severity" in fields_dict and isinstance(fields_dict["initial_severity"], str):
        val = fields_dict["initial_severity"].upper().strip()
        fields_dict["initial_severity"] = "CRITICAL" if "CRIT" in val else "MAJOR" if "MAJOR" in val else "MINOR"
    if "priority" in fields_dict and isinstance(fields_dict["priority"], str):
        val = fields_dict["priority"].upper().strip()
        fields_dict["priority"] = "HIGH" if "HIGH" in val else "MEDIUM" if "MED" in val else "LOW"


async def entity_extraction_node(state: GraphState) -> Dict[str, Any]:
    logger.info(f"[{state.get('request_id')}] Entity Extraction Node: Extracting entities")
    
    intent = state.get("detected_intent")
    if intent == "conversation":
        logger.info(f"[{state.get('request_id')}] Skipping extraction for conversation intent")
        return {}

    normalized_message = (state.get("user_message") or "").strip().lower().rstrip(".!?")
    confirmation_messages = {
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
    }
    if normalized_message in confirmation_messages and state.get("complaint_draft"):
        draft_service = DraftService()
        status_info = draft_service.validate(state["complaint_draft"])
        logger.info(f"[{state.get('request_id')}] Skipping extraction for confirmation-only message")
        return {
            "draft_status": status_info["status"].value,
            "changed_fields": [],
        }

    if settings.DEMO_OFFLINE_MODE or (state.get("metadata") or {}).get("llm_unavailable"):
        current_draft = state.get("complaint_draft") or ComplaintDraft()
        extracted_fields = _fallback_extract_fields(
            state.get("user_message", ""),
            update_mode=bool(current_draft and _is_update_message(state.get("user_message", ""))),
        )
        if current_draft and _is_update_message(state.get("user_message", "")):
            _sync_description_with_corrections(current_draft, extracted_fields)
        if not extracted_fields:
            return {}

        normalize_extracted_fields(extracted_fields)
        draft_service = DraftService()
        metadata_dict = {
            field: FieldMetadata(confidence=0.7, source="deterministic_demo")
            for field in extracted_fields
        }
        result = draft_service.merge(current_draft, extracted_fields, metadata=metadata_dict)
        status_info = draft_service.validate(result.updated_draft)
        metadata = state.get("metadata", {}).copy()
        metadata["llm_unavailable"] = True
        metadata["latest_extracted_fields"] = extracted_fields
        metadata["latest_field_metadata"] = {
            field: meta.model_dump()
            for field, meta in metadata_dict.items()
        }
        return {
            "complaint_draft": result.updated_draft,
            "changed_fields": result.changed_fields,
            "draft_status": status_info["status"].value,
            "metadata": metadata,
        }
        
    llm = get_llm_provider()
    extraction_prompt = load_prompt("entity_extraction.md")
    
    current_draft = state.get("complaint_draft")
    if not current_draft:
        current_draft = ComplaintDraft()
        
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
            "complaint_draft": draft,
            "changed_fields": all_changed_fields,
            "draft_status": draft_status,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"[{state.get('request_id')}] Entity Extraction Error: {e}")
        extracted_fields = _fallback_extract_fields(
            state.get("user_message", ""),
            update_mode=bool(current_draft and _is_update_message(state.get("user_message", ""))),
        )
        if current_draft and _is_update_message(state.get("user_message", "")):
            _sync_description_with_corrections(current_draft, extracted_fields)
        if not extracted_fields:
            return {}

        normalize_extracted_fields(extracted_fields)
        draft_service = DraftService()
        metadata_dict = {
            field: FieldMetadata(confidence=0.55, source="deterministic_fallback")
            for field in extracted_fields
        }
        result = draft_service.merge(current_draft, extracted_fields, metadata=metadata_dict)
        status_info = draft_service.validate(result.updated_draft)
        metadata = state.get("metadata", {}).copy()
        metadata["latest_extracted_fields"] = extracted_fields
        metadata["latest_field_metadata"] = {
            field: meta.model_dump()
            for field, meta in metadata_dict.items()
        }

        return {
            "complaint_draft": result.updated_draft,
            "changed_fields": result.changed_fields,
            "draft_status": status_info["status"].value,
            "metadata": metadata,
        }

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
    if metadata.get("awaiting_new_complaint_decision") and normalized_message in {
        "no",
        "n",
        "nope",
        "no thanks",
        "not now",
    }:
        metadata["awaiting_new_complaint_decision"] = False
    
    if hasattr(decision_output, "reset_context") and decision_output.reset_context:
        logger.info(f"[{state.get('request_id')}] Decision Node: Executing state reset for new workflow/pivot.")
        metadata["current_complaint_start_idx"] = metadata.get("message_count", 0)
        metadata["awaiting_new_complaint_decision"] = False
        
        # Completely clear old state
        updates["complaint_draft"] = None
        updates["clarification_state"] = None
        updates["selected_tool"] = None
        updates["pending_tool"] = None
        updates["tool_arguments"] = None
        
        # Apply fresh extraction directly to new draft
        latest_extracted = metadata.get("latest_extracted_fields")
        if latest_extracted:
            from app.services.draft_service import DraftService
            draft_service = DraftService()
            fresh_draft = ComplaintDraft()
            
            latest_meta = metadata.get("latest_field_metadata", {})
            meta_dict = {}
            for field, m in latest_meta.items():
                if field in latest_extracted:
                    meta_dict[field] = FieldMetadata(**m)
                    
            fresh_draft = draft_service.merge(fresh_draft, latest_extracted, metadata=meta_dict).updated_draft
            updates["complaint_draft"] = fresh_draft
            
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
        draft = state.get("complaint_draft")
        if draft:
            draft_dict = draft.model_dump(exclude_none=True)
            tool_schema_fields = tool.args_schema.model_fields.keys()
            tool_args = {k: v for k, v in draft_dict.items() if k in tool_schema_fields}
        else:
            tool_args = {}
            
        logger.info(f"[{state.get('request_id')}] Selected tool: {tool.name}")
        logger.info(f"[{state.get('request_id')}] Tool arguments mapped directly from ComplaintDraft")
        
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
        
    draft = state.get("complaint_draft")
    if not draft:
        logger.error(f"[{state.get('request_id')}] Workflow Invariant Violation: Tool execution attempted with no ComplaintDraft")
        return {"tool_status": "failed", "validation_errors": ["No ComplaintDraft found."]}
        
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

    if tool_name_value == "edit_complaint" and not tool_args.get("id"):
        active_complaint_id = (state.get("metadata") or {}).get("active_complaint_id")
        if not active_complaint_id:
            logger.warning(f"[{state.get('request_id')}] EditComplaint requested without an active complaint id.")
            return {
                "tool_status": "failed",
                "validation_errors": ["No active complaint is available to edit."],
                "conversation_status": ConversationStatus.COLLECTING_INFORMATION,
            }
        tool_args = {**tool_args, "id": active_complaint_id}
    
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
                metadata["active_complaint_id"] = str(result.get("id"))
            if result.get("complaint_number"):
                metadata["active_complaint"] = result.get("complaint_number")
            metadata["last_tool"] = tool_name_value
            if tool_name_value == "save_complaint":
                metadata["awaiting_new_complaint_decision"] = True

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

    if settings.DEMO_OFFLINE_MODE or (state.get("metadata") or {}).get("llm_unavailable"):
        response = fallback_templates.generate_fallback_response(state)
        if state.get("conversation_id"):
            await conversation_memory_service.append_message(state["conversation_id"], "assistant", response)
        return {"llm_response": response}
    
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
