from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """
    Standard API Response model.
    """
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[list[Any]] = None
