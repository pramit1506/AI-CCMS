from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema
from app.shared.enums import ComplaintStatus, ComplaintSource, Severity, Priority

class ComplaintBase(BaseSchema):
    complaint_number: str = Field(..., max_length=50)
    customer_id: UUID
    
    complaint_source: ComplaintSource
    
    product_name: str = Field(..., max_length=255)
    product_strength: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[str] = Field(None, max_length=50)
    
    complaint_type: Optional[str] = Field(None, max_length=100)
    complaint_date: date
    detailed_description: Optional[str] = None
    
    initial_severity: Optional[Severity] = None
    priority: Optional[Priority] = None
    
    # AI Risk Assessment
    risk_classification: Optional[str] = Field(None, max_length=100)
    root_cause_recommendation: Optional[str] = None
    capa_recommendation: Optional[str] = None
    risk_reasoning: Optional[str] = None

    status: ComplaintStatus = ComplaintStatus.PENDING_TRIAGE

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintUpdate(BaseModel):
    complaint_source: Optional[ComplaintSource] = None
    product_name: Optional[str] = Field(None, max_length=255)
    product_strength: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[str] = Field(None, max_length=50)
    complaint_type: Optional[str] = Field(None, max_length=100)
    complaint_date: Optional[date] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[Severity] = None
    priority: Optional[Priority] = None
    status: Optional[ComplaintStatus] = None
    risk_classification: Optional[str] = Field(None, max_length=100)
    root_cause_recommendation: Optional[str] = None
    capa_recommendation: Optional[str] = None
    risk_reasoning: Optional[str] = None

class ComplaintRead(ComplaintBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class ComplaintResponse(ComplaintRead):
    pass
