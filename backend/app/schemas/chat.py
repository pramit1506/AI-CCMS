from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from app.schemas.draft import InteractionDraft
from app.schemas.memory import ClarificationState, ConversationMetadata
from app.schemas.decision import DecisionOutput
from app.shared.enums import DraftStatus, ConversationStatus


class ChatRequest(BaseModel):
    user_message: str
    conversation_id: Optional[str] = None
    message_history: List[Dict[str, str]] = Field(default_factory=list)


class FieldChange(BaseModel):
    field_name: str
    previous_value: Optional[Any] = None
    current_value: Optional[Any] = None
    change_type: str  # "added", "updated", "removed"


class ToolExecutionResult(BaseModel):
    status: str
    created_resource_id: Optional[str] = None
    success_message: Optional[str] = None
    validation_warnings: List[str] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    assistant_message: str
    conversation_id: str
    interaction_draft: Optional[InteractionDraft] = None
    draft_status: Optional[DraftStatus] = None
    draft_changes: List[FieldChange] = Field(default_factory=list)
    clarification_state: Optional[ClarificationState] = None
    decision_output: Optional[DecisionOutput] = None
    tool_execution_result: Optional[ToolExecutionResult] = None
    conversation_status: ConversationStatus
    conversation_metadata: Optional[ConversationMetadata] = None
