from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.database.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.complaint import Complaint

class Customer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customer"

    customer_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint", back_populates="customer", cascade="all, delete-orphan"
    )
