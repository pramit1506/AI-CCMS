from typing import List, Dict, Any
from app.graph.state import GraphState
from app.shared.enums import AgentAction
import logging

logger = logging.getLogger(__name__)

class FallbackTemplateService:
    """Generates deterministic natural language responses from application state."""
    
    FIELD_PROMPTS = {
        "customer_name": "Who reported the complaint?",
        "complaint_source": "Was the complaint received by PDF, email, call, portal, or pasted text?",
        "product_name": "Which product is the complaint about?",
        "complaint_date": "What is the complaint date?",
        "detailed_description": "Could you provide the detailed complaint description?",
        "initial_severity": "What is the initial severity: critical, major, or minor?",
        "priority": "What is the priority: high, medium, or low?"
    }

    @classmethod
    def generate_clarification_response(cls, state: GraphState) -> str:
        """Generates a clarification response based on missing fields."""
        decision = state.get("decision_output")
        missing_fields = []
        
        if decision and hasattr(decision, "required_missing_fields") and decision.required_missing_fields:
            missing_fields = decision.required_missing_fields
        else:
            # Fallback to clarification state if available
            clarification = state.get("clarification_state")
            if clarification and hasattr(clarification, "missing_fields") and clarification.missing_fields:
                missing_fields = clarification.missing_fields

        if not missing_fields:
            return "I updated the complaint draft. What else would you like to add?"

        # Pick the first missing field to ask about
        target_field = missing_fields[0]
        specific_question = cls.FIELD_PROMPTS.get(target_field, f"Could you provide the {target_field.replace('_', ' ')}?")
        
        return specific_question

    @classmethod
    def generate_fallback_response(cls, state: GraphState) -> str:
        """Generates a contextual fallback response when the LLM is unavailable."""
        decision = state.get("decision_output")
        action = decision.action if decision and hasattr(decision, "action") else None
        
        if action == AgentAction.CLARIFY:
            return cls.generate_clarification_response(state)
        elif action == AgentAction.CONTINUE:
            changed_fields = state.get("changed_fields") or []
            if changed_fields:
                pretty_fields = ", ".join(field.replace("_", " ") for field in changed_fields)
                return f"Updated {pretty_fields}. Please review the form, then click Save Complaint when ready."
            draft_status = state.get("draft_status")
            if str(draft_status) == "READY" or (hasattr(draft_status, "value") and draft_status.value == "READY"):
                return "I extracted the complaint details and generated the initial risk assessment. Please review the form, then click Save Complaint when ready."
            return "I updated the complaint draft. Please provide any missing details so I can complete the form."
        elif action == AgentAction.EXECUTE_TOOL:
            validation_errors = state.get("validation_errors") or []
            if validation_errors:
                return f"I could not complete the action: {', '.join(str(error) for error in validation_errors)}"
            tool_result = state.get("tool_result") or {}
            if isinstance(tool_result, dict):
                message = tool_result.get("message")
                complaint_number = tool_result.get("complaint_number")
                if message:
                    return str(message)
                if complaint_number:
                    return f"Complaint saved successfully. Reference number: {complaint_number}."
            return "Action completed successfully."
        elif action == AgentAction.RESPOND:
            draft_status = state.get("draft_status")
            # DraftStatus might be a string or enum, handle both safely
            if str(draft_status) == "READY" or (hasattr(draft_status, "value") and draft_status.value == "READY"):
                return "The complaint draft is ready. Please review it and click Save Complaint when ready."
            return "I updated the complaint workflow. How else can I help?"
        
        # Generic fallback
        return "I updated the complaint workflow. Please continue with any additional details."

fallback_templates = FallbackTemplateService()
