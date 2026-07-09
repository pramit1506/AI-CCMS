from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any
from pydantic import BaseModel
from app.tools.context import ToolExecutionContext

InputSchema = TypeVar("InputSchema", bound=BaseModel)
OutputSchema = TypeVar("OutputSchema", bound=BaseModel)

class BaseTool(ABC):
    """Abstract base class for all LangGraph tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool (must be unique)."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does and when to use it."""
        pass
        
    @property
    @abstractmethod
    def args_schema(self) -> Type[BaseModel]:
        """Pydantic schema for the tool's inputs."""
        pass
        
    @property
    @abstractmethod
    def return_schema(self) -> Type[BaseModel]:
        """Pydantic schema for the tool's output."""
        pass
        
    def get_required_fields(self) -> list[str]:
        """Get a list of required fields based on args_schema."""
        return [k for k, f in self.args_schema.model_fields.items() if f.is_required()]
        
    def get_optional_fields(self) -> list[str]:
        """Get a list of optional fields based on args_schema."""
        return [k for k, f in self.args_schema.model_fields.items() if not f.is_required()]
        
    @abstractmethod
    async def execute(self, context: ToolExecutionContext, **kwargs) -> Any:
        """
        Execute the tool's core logic.
        
        Args:
            context: Execution context containing DB session, logger, etc.
            **kwargs: Validated arguments matching args_schema.
            
        Returns:
            An instance matching return_schema or a dict that can be parsed into it.
        """
        pass
