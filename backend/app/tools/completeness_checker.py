from pydantic import BaseModel
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext

class CompletenessInput(BaseModel):
    detailed_description: str
    product_name: str
    batch_number: str | None = None

class CompletenessOutput(BaseModel):
    is_complete: bool
    missing_critical_fields: list[str]
    message: str

class CompletenessCheckerTool(BaseTool):
    @property
    def name(self) -> str:
        return "completeness_check"
        
    @property
    def description(self) -> str:
        return "Check if the complaint has all required critical fields (like batch number)."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return CompletenessInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return CompletenessOutput

    def get_required_fields(self) -> list[str]:
        return ["product_name", "detailed_description"]
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        missing = []
        if not kwargs.get("batch_number"):
            missing.append("Batch/Lot Number is strongly recommended for QMS investigations.")
            
        return {
            "is_complete": len(missing) == 0,
            "missing_critical_fields": missing,
            "message": "Completeness check finished." if len(missing) == 0 else "Complaint is missing recommended QA fields."
        }
