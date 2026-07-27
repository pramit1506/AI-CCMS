from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.llm.factory import get_llm_provider

class SummarizeComplaintInput(BaseModel):
    detailed_description: str = Field(..., description="The full complaint description.")

class SummarizeComplaintOutput(BaseModel):
    summary: str
    message: str

class SummarizeComplaintTool(BaseTool):
    @property
    def name(self) -> str:
        return "summarize_complaint"
        
    @property
    def description(self) -> str:
        return "Summarize a long complaint description into a concise sentence."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return SummarizeComplaintInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return SummarizeComplaintOutput

    def get_required_fields(self) -> list[str]:
        return ["detailed_description"]
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        llm = get_llm_provider()
        prompt = f"Summarize this pharmaceutical complaint in one sentence: {kwargs['detailed_description']}"
        try:
            response = await llm.generate_response([{"role": "user", "content": prompt}])
        except Exception:
            response = kwargs["detailed_description"][:240]
        return {
            "summary": response,
            "message": "Summarization complete."
        }
