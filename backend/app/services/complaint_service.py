from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseService
from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from app.repositories.complaint_repository import complaint_repository
from app.repositories.customer_repository import customer_repository
from app.exceptions.base import ConflictException, ResourceNotFoundException
from app.shared.enums import ComplaintStatus, ComplaintSource

class ComplaintService(BaseService[Complaint, ComplaintCreate, ComplaintUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: ComplaintCreate) -> Complaint:
        existing_complaint = await self.repository.get_by_complaint_number(db, complaint_number=obj_in.complaint_number)
        if existing_complaint:
            raise ConflictException(f"Complaint with number {obj_in.complaint_number} already exists.")
            
        customer = await customer_repository.get_by_id(db, id=obj_in.customer_id)
        if not customer:
            raise ResourceNotFoundException(f"Customer with id {obj_in.customer_id} not found.")
                
        return await super().create(db, obj_in=obj_in)

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
        return await self.repository.get_paginated(
            db, 
            skip=skip, 
            limit=limit, 
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            complaint_source=complaint_source,
            sort_by=sort_by, 
            sort_desc=sort_desc
        )

complaint_service = ComplaintService(complaint_repository)
