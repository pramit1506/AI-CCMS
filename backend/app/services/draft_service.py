import copy
from typing import Dict, Any, List, Tuple
from app.schemas.draft import InteractionDraft, DraftUpdateResult, FieldMetadata
from app.shared.enums import DraftStatus

class DraftService:
    
    REQUIRED_FIELDS = [
        "hcp_id",
        "interaction_type",
        "interaction_date",
        "status",
        "discussion_summary"
    ]
    
    OPTIONAL_FIELDS = [
        "hcp_name",
        "interaction_time",
        "topics_discussed",
        "materials_shared",
        "sentiment",
        "follow_up_required",
        "follow_up_date",
        "attendees"
    ]

    def _is_empty_value(self, val: Any) -> bool:
        if val is None:
            return True
        if isinstance(val, str) and not val.strip():
            return True
        if isinstance(val, list) and len(val) == 0:
            return True
        return False

    def required_missing_fields(self, draft: InteractionDraft) -> List[str]:
        missing = []
        for field in self.REQUIRED_FIELDS:
            if field == "hcp_id":
                if self._is_empty_value(getattr(draft, "hcp_id", None)) and self._is_empty_value(getattr(draft, "hcp_name", None)):
                    missing.append("hcp_id")
            else:
                val = getattr(draft, field, None)
                if self._is_empty_value(val):
                    missing.append(field)
        return missing

    def optional_missing_fields(self, draft: InteractionDraft) -> List[str]:
        missing = []
        for field in self.OPTIONAL_FIELDS:
            val = getattr(draft, field, None)
            if self._is_empty_value(val):
                missing.append(field)
        return missing

    def is_ready(self, draft: InteractionDraft) -> bool:
        return len(self.required_missing_fields(draft)) == 0

    def calculate_status(self, draft: InteractionDraft) -> DraftStatus:
        req_missing = self.required_missing_fields(draft)
        
        all_fields = self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS
        has_any_data = any(not self._is_empty_value(getattr(draft, f, None)) for f in all_fields)
        
        if not has_any_data:
            return DraftStatus.EMPTY
            
        if len(req_missing) == 0:
            return DraftStatus.READY
            
        return DraftStatus.PARTIAL

    def validate_against_schema(self, draft: InteractionDraft, required_fields: List[str], optional_fields: List[str]) -> Dict[str, Any]:
        """
        Validates the draft dynamically against specific required and optional fields.
        """
        req_missing = []
        for field in required_fields:
            if field == "hcp_id":
                if self._is_empty_value(getattr(draft, "hcp_id", None)) and self._is_empty_value(getattr(draft, "hcp_name", None)):
                    req_missing.append("hcp_id")
            else:
                if self._is_empty_value(getattr(draft, field, None)):
                    req_missing.append(field)
                    
        opt_missing = []
        for field in optional_fields:
            if self._is_empty_value(getattr(draft, field, None)):
                opt_missing.append(field)
                
        is_ready = len(req_missing) == 0
        status = DraftStatus.READY if is_ready else DraftStatus.PARTIAL
        
        all_fields = required_fields + optional_fields
        if not any(not self._is_empty_value(getattr(draft, f, None)) for f in all_fields):
            status = DraftStatus.EMPTY
            
        return {
            "is_ready": is_ready,
            "status": status,
            "required_missing": req_missing,
            "optional_missing": opt_missing
        }

    def validate(self, draft: InteractionDraft) -> Dict[str, Any]:
        """
        Returns a summary of the validation state using the default fields.
        """
        return self.validate_against_schema(draft, self.REQUIRED_FIELDS, self.OPTIONAL_FIELDS)

    def _apply_update(self, draft: InteractionDraft, updates: Dict[str, Any], merge_lists: bool = True) -> Tuple[InteractionDraft, List[str]]:
        """
        Internal immutable update applier.
        """
        merged_data = copy.deepcopy(draft.model_dump())
        changed_fields = []
        
        for key, value in updates.items():
            if value is None:
                continue
                
            if key in merged_data:
                current_value = merged_data[key]
                if merge_lists and isinstance(current_value, list) and isinstance(value, list):
                    original_len = len(current_value)
                    for item in value:
                        if item not in current_value:
                            current_value.append(item)
                    merged_data[key] = current_value
                    if len(current_value) > original_len:
                        changed_fields.append(key)
                elif isinstance(current_value, dict) and isinstance(value, dict) and key != "field_metadata":
                    # Merge dicts
                    for k, v in value.items():
                        if k not in current_value or current_value[k] != v:
                            current_value[k] = v
                            if key not in changed_fields:
                                changed_fields.append(key)
                    merged_data[key] = current_value
                elif key == "field_metadata" and isinstance(value, dict):
                    current_metadata = merged_data.get("field_metadata", {})
                    for meta_key, meta_val in value.items():
                        if isinstance(meta_val, FieldMetadata):
                            current_metadata[meta_key] = meta_val.model_dump()
                        elif isinstance(meta_val, dict):
                            current_metadata[meta_key] = meta_val
                    merged_data["field_metadata"] = current_metadata
                else:
                    if current_value != value:
                        merged_data[key] = value
                        changed_fields.append(key)
        
        updated_draft = InteractionDraft(**merged_data)
        return updated_draft, changed_fields

    def merge(self, draft: InteractionDraft, extracted_fields: Dict[str, Any], metadata: Dict[str, FieldMetadata] = None) -> DraftUpdateResult:
        """
        Merges new extracted fields. Appends to lists, keeps existing valid data.
        """
        updates = copy.deepcopy(extracted_fields)
        if metadata:
            updates["field_metadata"] = metadata
            
        updated_draft, changed_fields = self._apply_update(draft, updates, merge_lists=True)
        return DraftUpdateResult(
            updated_draft=updated_draft,
            changed_fields=changed_fields,
            merge_summary=f"Merged {len(changed_fields)} fields."
        )

    def update_field(self, draft: InteractionDraft, field_name: str, value: Any, metadata: FieldMetadata = None) -> DraftUpdateResult:
        """
        Explicitly update a single field. Overwrites existing lists.
        """
        updates = {field_name: value}
        if metadata:
            updates["field_metadata"] = {field_name: metadata}
            
        updated_draft, changed_fields = self._apply_update(draft, updates, merge_lists=False)
        return DraftUpdateResult(
            updated_draft=updated_draft,
            changed_fields=changed_fields,
            merge_summary=f"Updated field {field_name}."
        )

    def remove_field(self, draft: InteractionDraft, field_name: str) -> DraftUpdateResult:
        """
        Clears a field's value.
        """
        merged_data = copy.deepcopy(draft.model_dump())
        changed_fields = []
        if field_name in merged_data:
            val = merged_data[field_name]
            if isinstance(val, list):
                merged_data[field_name] = []
            elif isinstance(val, dict):
                merged_data[field_name] = {}
            else:
                merged_data[field_name] = None
            changed_fields.append(field_name)
            
            if "field_metadata" in merged_data and field_name in merged_data["field_metadata"]:
                del merged_data["field_metadata"][field_name]

        updated_draft = InteractionDraft(**merged_data)
        return DraftUpdateResult(
            updated_draft=updated_draft,
            changed_fields=changed_fields,
            merge_summary=f"Removed field {field_name}."
        )

    def correct_field(self, draft: InteractionDraft, field_name: str, value: Any, metadata: FieldMetadata = None) -> DraftUpdateResult:
        """
        Alias for update_field for conversational corrections.
        """
        return self.update_field(draft, field_name, value, metadata)
