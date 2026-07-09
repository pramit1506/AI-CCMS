import warnings
from typing import Dict, Any
from app.schemas.draft import InteractionDraft
from app.services.draft_service import DraftService

def merge_draft(existing_draft: InteractionDraft, extracted_fields: Dict[str, Any]) -> InteractionDraft:
    """
    DEPRECATED: Use DraftService.merge() instead.
    
    Merge newly extracted fields into an existing InteractionDraft.
    """
    warnings.warn(
        "merge_draft is deprecated. Use DraftService().merge() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    service = DraftService()
    if not existing_draft:
        existing_draft = InteractionDraft()
    result = service.merge(existing_draft, extracted_fields)
    return result.updated_draft
