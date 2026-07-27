from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.tools.registry import tool_registry

from app.tools.save_complaint import SaveComplaintTool
from app.tools.edit_complaint import EditComplaintTool
from app.tools.recommend_capa import RecommendCapaTool
from app.tools.summarize_complaint import SummarizeComplaintTool
from app.tools.completeness_checker import CompletenessCheckerTool

# Register all tools
tool_registry.register(SaveComplaintTool())
tool_registry.register(EditComplaintTool())
tool_registry.register(RecommendCapaTool())
tool_registry.register(SummarizeComplaintTool())
tool_registry.register(CompletenessCheckerTool())

__all__ = ["BaseTool", "ToolExecutionContext", "tool_registry"]
