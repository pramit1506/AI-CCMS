from typing import TYPE_CHECKING
from datetime import date
import uuid
from sqlalchemy import String, Date, ForeignKey, Enum as SQLEnum, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.database.mixins import UUIDMixin, TimestampMixin
from app.shared.enums import ComplaintStatus, ComplaintSource, Severity, Priority

if TYPE_CHECKING:
    from app.models.customer import Customer

class Complaint(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "complaint"

    complaint_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customer.id"), index=True)
    
    # Origin & Customer Details
    complaint_source: Mapped[ComplaintSource] = mapped_column(SQLEnum(ComplaintSource))
    
    # Product & Batch Identification
    product_name: Mapped[str] = mapped_column(String(255))
    product_strength: Mapped[str | None] = mapped_column(String(100))
    batch_number: Mapped[str | None] = mapped_column(String(100), index=True)
    manufacturing_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    quantity_affected: Mapped[str | None] = mapped_column(String(50)) # e.g. "50 kg"
    
    # Complaint Details
    complaint_type: Mapped[str | None] = mapped_column(String(100))
    complaint_date: Mapped[date] = mapped_column(Date, index=True)
    detailed_description: Mapped[str | None] = mapped_column(Text)
    
    # Initial Assessment & Priority
    initial_severity: Mapped[Severity | None] = mapped_column(SQLEnum(Severity))
    priority: Mapped[Priority | None] = mapped_column(SQLEnum(Priority))
    
    # State
    status: Mapped[ComplaintStatus] = mapped_column(SQLEnum(ComplaintStatus), index=True, default=ComplaintStatus.PENDING_TRIAGE)

    # AI Risk Assessment
    risk_classification: Mapped[str | None] = mapped_column(String(100))
    root_cause_recommendation: Mapped[str | None] = mapped_column(Text)
    capa_recommendation: Mapped[str | None] = mapped_column(Text)
    risk_reasoning: Mapped[str | None] = mapped_column(Text)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="complaints")
