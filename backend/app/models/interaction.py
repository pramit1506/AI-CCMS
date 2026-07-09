from typing import TYPE_CHECKING
from datetime import date
import uuid
from sqlalchemy import String, Date, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.database.mixins import UUIDMixin, TimestampMixin
from app.shared.enums import InteractionStatus, InteractionType

if TYPE_CHECKING:
    from app.models.hcp import HCP

class Interaction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "interaction"

    interaction_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hcp_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hcp.id"), index=True)
    interaction_date: Mapped[date] = mapped_column(Date, index=True)
    
    interaction_type: Mapped[InteractionType] = mapped_column(SQLEnum(InteractionType))
    status: Mapped[InteractionStatus] = mapped_column(SQLEnum(InteractionStatus), index=True)
    
    discussion_summary: Mapped[str | None] = mapped_column(Text)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_date: Mapped[date | None] = mapped_column(Date)

    # Relationships
    hcp: Mapped["HCP"] = relationship("HCP", back_populates="interactions")
