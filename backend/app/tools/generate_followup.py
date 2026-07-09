from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.shared.enums import InteractionType
from app.llm.factory import get_llm_provider

class GenerateFollowupInput(BaseModel):
    discussion_summary: str = Field(..., description="The summary of the discussion that requires a follow-up.")
    interaction_type: InteractionType = Field(..., description="The type of the original interaction.")

class GenerateFollowupOutput(BaseModel):
    suggested_action: str = Field(..., description="The suggested follow-up action.")
    suggested_date_offset_days: int = Field(..., description="Suggested number of days until the follow-up.")
    reasoning: str = Field(..., description="Reasoning for the suggested follow-up.")

class GenerateFollowupTool(BaseTool):
    @property
    def name(self) -> str:
        return "generate_followup"
        
    @property
    def description(self) -> str:
        return "Generate a suggested follow-up recommendation based on an interaction's discussion summary."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return GenerateFollowupInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return GenerateFollowupOutput
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        context.logger.info(f"[{context.request_id}] Executing GenerateFollowupTool")
        
        prompt = f"""
        Based on the following interaction summary, suggest a follow-up action and when it should happen.
        
        Interaction Type: {kwargs['interaction_type']}
        Discussion Summary: {kwargs['discussion_summary']}
        
        Provide the suggested action, an offset in days from the original interaction (e.g., 7 for one week later), and the reasoning.
        """
        
        llm = context.llm_provider or get_llm_provider()
        
        messages = [{"role": "user", "content": prompt}]
        
        result = await llm.generate_structured(messages=messages, schema=GenerateFollowupOutput)
        
        return result.model_dump()
