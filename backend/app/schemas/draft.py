from typing import List, Optional, Dict, Any
from datetime import date, time, datetime, timezone
from pydantic import BaseModel, Field
from app.shared.enums import ComplaintStatus, ComplaintSource, Severity, Priority

def get_utc_now():
    return datetime.now(timezone.utc)

class FieldMetadata(BaseModel):
    value: Any = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    last_updated: Optional[datetime] = Field(default_factory=get_utc_now)

class ComplaintDraft(BaseModel):
    # Origin & Customer Details
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    complaint_source: Optional[ComplaintSource] = None
    
    # Product & Batch Identification
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quantity_affected: Optional[str] = None
    
    # Complaint Details
    complaint_type: Optional[str] = None
    complaint_date: Optional[date] = None
    detailed_description: Optional[str] = None
    
    # Initial Assessment & Priority
    initial_severity: Optional[Severity] = None
    priority: Optional[Priority] = None
    
    # State
    status: Optional[ComplaintStatus] = None
    
    # AI Risk Assessment
    risk_classification: Optional[str] = None
    root_cause_recommendation: Optional[str] = None
    capa_recommendation: Optional[str] = None
    risk_reasoning: Optional[str] = None
    
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    field_metadata: Dict[str, FieldMetadata] = Field(default_factory=dict)

class DraftUpdateResult(BaseModel):
    updated_draft: ComplaintDraft
    changed_fields: List[str]
    merge_summary: str
