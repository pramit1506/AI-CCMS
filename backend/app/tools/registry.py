from typing import Dict, List, Optional
from app.tools.base_tool import BaseTool
from loguru import logger

class ToolRegistry:
    """Registry for managing and resolving tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool) -> None:
        """Register a new tool."""
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is already registered. Overwriting.")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)
        
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())
        
    def get_tool_descriptions(self) -> str:
        """Get a formatted string of all tools and their descriptions (useful for prompts)."""
        descriptions = []
        for tool in self._tools.values():
            schema_fields = tool.args_schema.model_json_schema().get("properties", {})
            required_fields = tool.args_schema.model_json_schema().get("required", [])
            
            field_desc = "\n".join([
                f"  - {field} ({'required' if field in required_fields else 'optional'}): {props.get('description', '')}" 
                for field, props in schema_fields.items()
            ])
            
            descriptions.append(f"Tool: {tool.name}\nDescription: {tool.description}\nArguments:\n{field_desc}")
            
        return "\n\n".join(descriptions)

# Global registry instance
tool_registry = ToolRegistry()
