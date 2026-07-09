from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.database.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.interaction import Interaction

class HCP(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "hcp"

    hcp_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    specialization: Mapped[str | None] = mapped_column(String(100))
    hospital_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction", back_populates="hcp", cascade="all, delete-orphan"
    )
