from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from app.shared.enums import ComplaintStatus, ComplaintSource, Severity, Priority

class RepositoryComplaint(BaseRepository[Complaint, ComplaintCreate, ComplaintUpdate]):
    async def get_by_complaint_number(self, db: AsyncSession, complaint_number: str) -> Optional[Complaint]:
        query = select(self.model).where(self.model.complaint_number == complaint_number)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[ComplaintStatus] = None,
        complaint_source: Optional[ComplaintSource] = None,
        sort_by: str = "complaint_date",
        sort_desc: bool = True
    ) -> tuple[List[Complaint], int]:
        query = select(self.model)
        
        if customer_id:
            query = query.where(self.model.customer_id == customer_id)
        if start_date:
            query = query.where(self.model.complaint_date >= start_date)
        if end_date:
            query = query.where(self.model.complaint_date <= end_date)
        if status:
            query = query.where(self.model.status == status)
        if complaint_source:
            query = query.where(self.model.complaint_source == complaint_source)
            
        sort_column = getattr(self.model, sort_by, self.model.complaint_date)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
            
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        
        return list(result.scalars().all()), total

complaint_repository = RepositoryComplaint(Complaint)
