from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel
from app.schemas.draft import ComplaintDraft
from app.schemas.decision import DecisionOutput
from app.shared.enums import AgentState, ToolName, ConversationStatus
from app.schemas.memory import ClarificationState
class IntentOutput(BaseModel):
    intent: str
    confidence: float
    
class ToolSelectionOutput(BaseModel):
    tool_name: Optional[ToolName] = None
    tool_arguments: Optional[Dict[str, Any]] = None

class GraphState(TypedDict):
    complaint_draft: Optional[ComplaintDraft]
    changed_fields: Optional[List[str]]
    draft_status: Optional[str]
    conversation_id: str
    request_id: str
    user_message: str
    clarification_state: Optional[ClarificationState]
    detected_intent: Optional[str]
    selected_tool: Optional[ToolName]
    pending_tool: Optional[ToolName]
    tool_arguments: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    tool_status: Optional[str]
    validation_errors: Optional[List[str]]
    clarification_reason: Optional[str]
    required_missing_fields: Optional[List[str]]
    optional_missing_fields: Optional[List[str]]
    decision_output: Optional[DecisionOutput]
    current_agent_state: Optional[AgentState]
    llm_response: Optional[str]
    metadata: Dict[str, Any]
    model_name: str
    conversation_status: Optional[ConversationStatus]
