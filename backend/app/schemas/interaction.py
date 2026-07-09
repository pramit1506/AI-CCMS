from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema
from app.shared.enums import InteractionStatus, InteractionType

class InteractionBase(BaseSchema):
    interaction_number: str = Field(..., max_length=50)
    hcp_id: UUID
    interaction_date: date
    interaction_type: InteractionType
    status: InteractionStatus
    discussion_summary: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    interaction_date: Optional[date] = None
    interaction_type: Optional[InteractionType] = None
    status: Optional[InteractionStatus] = None
    discussion_summary: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None

class InteractionRead(InteractionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class InteractionResponse(InteractionRead):
    pass
