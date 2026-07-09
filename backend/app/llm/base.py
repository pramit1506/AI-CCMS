from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseLLMProvider(ABC):
    """Abstract base class for LLM Providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: list[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a raw string response from the LLM."""
        pass
        
    @abstractmethod
    async def generate_structured(
        self,
        messages: list[Dict[str, Any]],
        schema: Type[T],
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> T:
        """Generate a structured response adhering to a Pydantic schema."""
        pass
