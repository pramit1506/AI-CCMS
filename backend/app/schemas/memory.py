from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
from pydantic import BaseModel, Field, field_validator

def get_utc_now():
    return datetime.now(timezone.utc)

from app.shared.enums import ClarificationLifecycle

class ClarificationState(BaseModel):
    tool_name: str = Field(..., description="The tool that required clarification")
    required_fields: List[str] = Field(default_factory=list, description="Fields required for the tool")
    missing_fields: List[str] = Field(default_factory=list, description="Fields that are still missing")
    resolved_fields: Dict[str, Any] = Field(default_factory=dict, description="Fields that have been resolved so far")
    clarification_reason: Optional[str] = Field(None, description="The reason clarification was requested")
    original_request: str = Field(..., description="The original user request that triggered the clarification")
    status: ClarificationLifecycle = Field(ClarificationLifecycle.CREATED, description="Lifecycle status of this clarification")

class ConversationSummary(BaseModel):
    active_hcps: List[str] = Field(default_factory=list)
    hospitals: List[str] = Field(default_factory=list)
    past_interactions: List[str] = Field(default_factory=list)
    pending_work: List[str] = Field(default_factory=list)
    resolved_clarifications: List[str] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=get_utc_now)

    @field_validator(
        "active_hcps",
        "hospitals",
        "past_interactions",
        "pending_work",
        "resolved_clarifications",
        mode="before",
    )
    @classmethod
    def stringify_summary_items(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        return [
            item if isinstance(item, str) else json.dumps(item, default=str)
            for item in value
        ]

class ConversationMetadata(BaseModel):
    active_hcp: Optional[str] = None
    active_hospital: Optional[str] = None
    active_interaction: Optional[str] = None
    last_followup: Optional[str] = None
    last_tool: Optional[str] = None
    conversation_start: datetime = Field(default_factory=get_utc_now)
    last_activity: datetime = Field(default_factory=get_utc_now)
    message_count: int = 0
    estimated_tokens: int = 0

class ResolvedContext(BaseModel):
    resolved_entities: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(0.0, description="Confidence score of the resolution (0.0 to 1.0)")
    requires_clarification: bool = Field(False, description="True if confidence is too low and clarification is needed")

class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=get_utc_now)
