from uuid import UUID
from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.services.interaction_service import interaction_service
from app.llm.factory import get_llm_provider

class SummarizeInteractionInput(BaseModel):
    hcp_id: UUID = Field(..., description="The unique identifier (UUID) of the Healthcare Professional to summarize interactions for.")
    limit: int = Field(5, description="Number of recent interactions to summarize.")

class SummarizeInteractionOutput(BaseModel):
    executive_summary: str = Field(..., description="The executive summary of the interactions.")
    key_takeaways: list[str] = Field(..., description="Key takeaways from the interactions.")

class SummarizeInteractionTool(BaseTool):
    @property
    def name(self) -> str:
        return "summarize_interaction"
        
    @property
    def description(self) -> str:
        return "Summarize the interaction history for a given Healthcare Professional (HCP)."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return SummarizeInteractionInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return SummarizeInteractionOutput
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        hcp_id = kwargs["hcp_id"]
        limit = kwargs.get("limit", 5)
        context.logger.info(f"[{context.request_id}] Executing SummarizeInteractionTool for HCP {hcp_id}")
        
        interactions, _ = await interaction_service.get_paginated(
            context.db, hcp_id=hcp_id, limit=limit, sort_by="interaction_date", sort_desc=True
        )
        
        if not interactions:
            return {
                "executive_summary": "No interactions found for this HCP.",
                "key_takeaways": []
            }
            
        history_text = ""
        for inter in interactions:
            history_text += f"- Date: {inter.interaction_date}, Type: {inter.interaction_type.value}, Status: {inter.status.value}\n"
            history_text += f"  Summary: {inter.discussion_summary}\n\n"
            
        prompt = f"""
        Please provide an executive summary and key takeaways for the following interaction history with a Healthcare Professional.
        
        Interaction History:
        {history_text}
        """
        
        llm = context.llm_provider or get_llm_provider()
        messages = [{"role": "user", "content": prompt}]
        
        result = await llm.generate_structured(messages=messages, schema=SummarizeInteractionOutput)
        return result.model_dump()
