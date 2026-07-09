import uuid
from typing import Any

def validate_uuid(value: Any) -> uuid.UUID:
    """Placeholder: Validate that the value is a valid UUID."""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))

def validate_non_empty_string(value: str) -> str:
    """Placeholder: Validate that the string is not empty."""
    if not value or not value.strip():
        raise ValueError("String cannot be empty")
    return value.strip()
