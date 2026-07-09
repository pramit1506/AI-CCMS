from typing import Optional
from datetime import date
import uuid
from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.schemas.interaction import InteractionCreate
from app.shared.enums import InteractionStatus, InteractionType
from app.services.interaction_service import interaction_service

class LogInteractionInput(BaseModel):
    hcp_id: Optional[str] = Field(None, description="The UUID or business identifier/code of the Healthcare Professional.")
    hcp_name: Optional[str] = Field(None, description="The name of the Healthcare Professional (if UUID is unknown).")
    interaction_date: date = Field(..., description="The date of the interaction (YYYY-MM-DD).")
    interaction_type: InteractionType = Field(..., description="The type of interaction (e.g., IN_PERSON, VIRTUAL, EMAIL, PHONE).")
    status: InteractionStatus = Field(..., description="The status of the interaction (e.g., PLANNED, COMPLETED, CANCELLED, NO_SHOW).")
    discussion_summary: Optional[str] = Field(None, description="A summary of what was discussed.")
    follow_up_required: bool = Field(False, description="Whether a follow-up is required.")
    follow_up_date: Optional[date] = Field(None, description="The date for the follow-up if required.")

class LogInteractionOutput(BaseModel):
    id: Optional[str]
    interaction_number: Optional[str]
    status: str
    message: str

class LogInteractionTool(BaseTool):
    @property
    def name(self) -> str:
        return "log_interaction"
        
    @property
    def description(self) -> str:
        return "Create a new interaction record for a Healthcare Professional (HCP)."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return LogInteractionInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return LogInteractionOutput

    def get_required_fields(self) -> list[str]:
        return [
            "hcp_id",
            "interaction_date",
            "interaction_type",
            "status",
            "discussion_summary",
        ]
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        context.logger.info(f"[{context.request_id}] Executing LogInteractionTool for HCP {kwargs.get('hcp_name') or kwargs.get('hcp_id')}")
        
        from app.services.hcp_resolution import hcp_resolution_service
        hcp_id_str = str(kwargs["hcp_id"]) if kwargs.get("hcp_id") else None
        hcp, error_msg = await hcp_resolution_service.resolve_hcp(context.db, hcp_name=kwargs.get("hcp_name"), hcp_id=hcp_id_str)
        
        if not hcp:
            return {
                "id": None,
                "interaction_number": None,
                "status": "failed",
                "message": error_msg or "Failed to resolve HCP."
            }
            
        interaction_number = f"INT-{uuid.uuid4().hex[:8].upper()}"
        
        create_schema = InteractionCreate(
            interaction_number=interaction_number,
            hcp_id=hcp.id,
            interaction_date=kwargs["interaction_date"],
            interaction_type=kwargs["interaction_type"],
            status=kwargs["status"],
            discussion_summary=kwargs.get("discussion_summary"),
            follow_up_required=kwargs.get("follow_up_required", False),
            follow_up_date=kwargs.get("follow_up_date")
        )
        
        interaction = await interaction_service.create(context.db, obj_in=create_schema)
        
        return {
            "id": str(interaction.id),
            "interaction_number": interaction.interaction_number,
            "status": interaction.status.value,
            "message": "Interaction successfully logged."
        }
