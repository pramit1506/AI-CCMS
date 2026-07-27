# Complaint Draft

The Complaint Draft represents the AI's current, evolving understanding of the complaint between an Customer and a user throughout a conversational session. It serves as the single source of truth for the session state and will eventually populate the React UI form on the frontend.

## Architecture & Lifecycle

1. **Initialization**: When a conversation starts or a new intent indicates complaint logging, an `InteractionDraft` is instantiated. It is added to the `GraphState`. The draft is a pure Pydantic model (`app.schemas.draft.InteractionDraft`).
2. **Updates & Extraction**: As the conversation progresses, new information is extracted by the LLM. This information is merged into the draft using `app.services.draft_service.DraftService`.
3. **DraftService (Immutability)**: Every operation (`merge`, `update_field`, `remove_field`, `correct_field`) via the `DraftService` returns a `DraftUpdateResult` containing a fresh `InteractionDraft` copy, the list of `changed_fields`, and a `merge_summary`. This guarantees immutability, which is essential for deterministic LangGraph state transitions.
4. **Validation & Status**: `DraftService.validate(draft)` analyzes the draft against strictly required and optional fields. It automatically derives a `DraftStatus` (`EMPTY`, `PARTIAL`, `READY`, `CONFIRMED`, `SAVED`).
5. **Completion**: Once the draft is `READY` (or manually marked as `CONFIRMED`) and the conversation concludes, the draft will be finalized and submitted to the database in later phases.

## GraphState Integration

The `GraphState` now includes an `interaction_draft` field:
```python
class GraphState(TypedDict):
    interaction_draft: Optional[InteractionDraft]
    # ... other fields
```

## Immutable Draft Updates & Change Tracking

The `DraftService` provides the public API for all updates. Updates return a `DraftUpdateResult`:
- `updated_draft`: The new `InteractionDraft` instance.
- `changed_fields`: A list of strings identifying exactly which fields were modified. This enables granular frontend state updates.
- `merge_summary`: Human-readable summary of the operation.

## Field Metadata

In addition to basic scalar fields (e.g., `interaction_type`, `hcp_id`), the `InteractionDraft` includes `field_metadata: Dict[str, FieldMetadata]`.
`FieldMetadata` tracks:
- `confidence`: LLM confidence score for the extraction.
- `source`: The source of the value (e.g., LLM vs. explicit User UI correction).
- `last_updated`: Timestamp of the change.

This structure allows rich metadata tracking without breaking backward compatibility for nodes or clients relying on the flat schema properties.
