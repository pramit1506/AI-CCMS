from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.tools.registry import tool_registry

from app.tools.log_interaction import LogInteractionTool
from app.tools.edit_interaction import EditInteractionTool
from app.tools.generate_followup import GenerateFollowupTool
from app.tools.summarize_interaction import SummarizeInteractionTool
from app.tools.compliance_checker import ComplianceCheckerTool

# Register all tools
tool_registry.register(LogInteractionTool())
tool_registry.register(EditInteractionTool())
tool_registry.register(GenerateFollowupTool())
tool_registry.register(SummarizeInteractionTool())
tool_registry.register(ComplianceCheckerTool())

__all__ = ["BaseTool", "ToolExecutionContext", "tool_registry"]
