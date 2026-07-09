from typing import List, Dict, Any
from app.graph.state import GraphState
from app.shared.enums import AgentAction
import logging

logger = logging.getLogger(__name__)

class FallbackTemplateService:
    """Generates deterministic natural language responses from application state."""
    
    FIELD_PROMPTS = {
        "interaction_type": "What type of interaction was it? (e.g. In person, virtual)",
        "interaction_date": "When did this interaction happen?",
        "status": "What was the status or outcome of the interaction?",
        "discussion_summary": "Could you briefly summarize what was discussed?",
        "hcp_name": "Which healthcare professional was this interaction with?",
        "hcp_id": "Which healthcare professional was this interaction with?"
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
            return "I'm temporarily having trouble generating a natural response, but we can continue. What else would you like to add?"

        # Pick the first missing field to ask about
        target_field = missing_fields[0]
        specific_question = cls.FIELD_PROMPTS.get(target_field, f"Could you provide the {target_field.replace('_', ' ')}?")
        
        return f"I'm temporarily having trouble generating a natural response, but we can continue logging your interaction. {specific_question}"

    @classmethod
    def generate_fallback_response(cls, state: GraphState) -> str:
        """Generates a contextual fallback response when the LLM is unavailable."""
        decision = state.get("decision_output")
        action = decision.action if decision and hasattr(decision, "action") else None
        
        if action == AgentAction.CLARIFY:
            return cls.generate_clarification_response(state)
        elif action == AgentAction.EXECUTE_TOOL:
            return "I'm temporarily having trouble generating a natural response, but I've successfully completed the action."
        elif action == AgentAction.RESPOND:
            draft_status = state.get("draft_status")
            # DraftStatus might be a string or enum, handle both safely
            if str(draft_status) == "READY" or (hasattr(draft_status, "value") and draft_status.value == "READY"):
                return "I'm temporarily having trouble generating a natural response, but I have everything I need. Should I proceed?"
            return "I'm temporarily having trouble generating a natural response. How else can I help?"
        
        # Generic fallback
        return "I'm temporarily having trouble generating a natural response. Could you please rephrase or continue?"

fallback_templates = FallbackTemplateService()
