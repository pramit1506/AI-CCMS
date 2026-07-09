from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime
from datetime import datetime
import uuid
from app.utils.datetime_utils import get_utc_now
from app.utils.uuid_utils import generate_uuid4

class UUIDMixin:
    """Provides a UUID4 primary key for models."""
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=generate_uuid4)

class TimestampMixin:
    """Provides created_at and updated_at timezone-aware timestamps."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now
    )
