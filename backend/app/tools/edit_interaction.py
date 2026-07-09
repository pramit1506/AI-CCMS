from typing import Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.schemas.interaction import InteractionUpdate
from app.shared.enums import InteractionStatus, InteractionType
from app.services.interaction_service import interaction_service

class EditInteractionInput(BaseModel):
    id: UUID = Field(..., description="The unique identifier (UUID) of the interaction to update.")
    interaction_date: Optional[date] = Field(None, description="The updated date of the interaction (YYYY-MM-DD).")
    interaction_type: Optional[InteractionType] = Field(None, description="The updated type of interaction (e.g., IN_PERSON, VIRTUAL, EMAIL, PHONE).")
    status: Optional[InteractionStatus] = Field(None, description="The updated status of the interaction (e.g., PLANNED, COMPLETED, CANCELLED, NO_SHOW).")
    discussion_summary: Optional[str] = Field(None, description="The updated summary of what was discussed.")
    follow_up_required: Optional[bool] = Field(None, description="Whether a follow-up is now required.")
    follow_up_date: Optional[date] = Field(None, description="The updated date for the follow-up if required.")

class EditInteractionOutput(BaseModel):
    id: str
    interaction_number: str
    status: str
    message: str

class EditInteractionTool(BaseTool):
    @property
    def name(self) -> str:
        return "edit_interaction"
        
    @property
    def description(self) -> str:
        return "Update an existing interaction record for a Healthcare Professional (HCP)."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return EditInteractionInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return EditInteractionOutput

    def get_required_fields(self) -> list[str]:
        # The active interaction id is supplied from conversation metadata when
        # editing immediately after logging an interaction.
        return []
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        interaction_id = kwargs.pop("id")
        context.logger.info(f"[{context.request_id}] Executing EditInteractionTool for Interaction {interaction_id}")
        
        # Remove None values so Pydantic doesn't override with explicit Nones if not intended
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        update_schema = InteractionUpdate(**update_data)
        
        interaction = await interaction_service.update(context.db, id=interaction_id, obj_in=update_schema)
        
        return {
            "id": str(interaction.id),
            "interaction_number": interaction.interaction_number,
            "status": interaction.status.value,
            "message": "Interaction successfully updated."
        }
