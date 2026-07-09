from typing import List, Optional, Dict, Any
from datetime import date, time, datetime, timezone
from pydantic import BaseModel, Field
from app.shared.enums import InteractionStatus, InteractionType

def get_utc_now():
    return datetime.now(timezone.utc)

class FieldMetadata(BaseModel):
    value: Any = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    last_updated: Optional[datetime] = Field(default_factory=get_utc_now)

class InteractionDraft(BaseModel):
    hcp_id: Optional[str] = None
    hcp_name: Optional[str] = None
    interaction_type: Optional[InteractionType] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    discussion_summary: Optional[str] = None
    topics_discussed: List[str] = Field(default_factory=list)
    materials_shared: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None
    attendees: List[str] = Field(default_factory=list)
    status: Optional[InteractionStatus] = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    # New dictionary for rich field metadata without breaking existing scalar fields
    field_metadata: Dict[str, FieldMetadata] = Field(default_factory=dict)

class DraftUpdateResult(BaseModel):
    updated_draft: InteractionDraft
    changed_fields: List[str]
    merge_summary: str
