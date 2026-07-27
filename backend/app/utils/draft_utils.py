import warnings
from typing import Dict, Any
from app.schemas.draft import ComplaintDraft
from app.services.draft_service import DraftService

def merge_draft(existing_draft: ComplaintDraft, extracted_fields: Dict[str, Any]) -> ComplaintDraft:
    """
    DEPRECATED: Use DraftService.merge() instead.
    
    Merge newly extracted fields into an existing ComplaintDraft.
    """
    warnings.warn(
        "merge_draft is deprecated. Use DraftService().merge() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    service = DraftService()
    if not existing_draft:
        existing_draft = ComplaintDraft()
    result = service.merge(existing_draft, extracted_fields)
    return result.updated_draft
