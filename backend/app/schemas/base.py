from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base schema with from_attributes set to True for ORM compatibility."""
    model_config = ConfigDict(from_attributes=True)
