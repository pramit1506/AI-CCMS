from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ExtractionOutput(BaseModel):
    """
    Schema for the LLM output during Entity Extraction.
    Only structured fields are returned to drive application logic.
    """
    extracted_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Newly extracted or explicitly updated Complaint fields. Only include fields that were explicitly mentioned or strongly implied."
    )
    corrections: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fields that the user explicitly wants to correct. Maps the field name to the new corrected value."
    )
    removed_fields: List[str] = Field(
        default_factory=list,
        description="Fields that the user explicitly wants to clear or remove."
    )
    field_metadata: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadata for any extracted or corrected fields. The key should match the field name. Include 'confidence' (float 0.0-1.0) and 'source' (e.g. 'user_message')."
    )
