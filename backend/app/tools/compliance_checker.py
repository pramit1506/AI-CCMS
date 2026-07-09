from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.shared.enums import InteractionStatus

class ComplianceCheckerInput(BaseModel):
    interaction_date: Optional[date] = Field(None, description="The date of the interaction.")
    status: Optional[InteractionStatus] = Field(None, description="The status of the interaction.")
    discussion_summary: Optional[str] = Field(None, description="The summary of what was discussed.")
    follow_up_required: Optional[bool] = Field(None, description="Whether a follow-up is required.")
    follow_up_date: Optional[date] = Field(None, description="The date for the follow-up if required.")

class ComplianceIssue(BaseModel):
    field: str
    issue: str
    severity: str

class ComplianceCheckerOutput(BaseModel):
    is_compliant: bool
    issues: list[ComplianceIssue]

class ComplianceCheckerTool(BaseTool):
    @property
    def name(self) -> str:
        return "compliance_check"
        
    @property
    def description(self) -> str:
        return "Review an interaction for compliance issues (e.g., missing summary, invalid dates)."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return ComplianceCheckerInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return ComplianceCheckerOutput
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        context.logger.info(f"[{context.request_id}] Executing ComplianceCheckerTool")
        
        issues = []
        
        status = kwargs.get("status")
        discussion_summary = kwargs.get("discussion_summary")
        interaction_date = kwargs.get("interaction_date")
        follow_up_required = kwargs.get("follow_up_required")
        follow_up_date = kwargs.get("follow_up_date")
        
        if status == InteractionStatus.COMPLETED and not discussion_summary:
            issues.append(ComplianceIssue(
                field="discussion_summary",
                issue="Discussion summary is required when status is COMPLETED.",
                severity="HIGH"
            ))
            
        if follow_up_required and not follow_up_date:
            issues.append(ComplianceIssue(
                field="follow_up_date",
                issue="Follow-up date is required when follow-up is marked as required.",
                severity="HIGH"
            ))
            
        if follow_up_date and interaction_date and follow_up_date < interaction_date:
            issues.append(ComplianceIssue(
                field="follow_up_date",
                issue="Follow-up date cannot precede the interaction date.",
                severity="HIGH"
            ))
            
        return {
            "is_compliant": len(issues) == 0,
            "issues": [issue.model_dump() for issue in issues]
        }
