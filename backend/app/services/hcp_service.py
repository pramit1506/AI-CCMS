from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseService
from app.models.hcp import HCP
from app.schemas.hcp import HCPCreate, HCPUpdate
from app.repositories.hcp_repository import hcp_repository
from app.exceptions.base import ConflictException

class HCPService(BaseService[HCP, HCPCreate, HCPUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: HCPCreate) -> HCP:
        existing_hcp = await self.repository.get_by_hcp_code(db, hcp_code=obj_in.hcp_code)
        if existing_hcp:
            raise ConflictException(f"HCP with code {obj_in.hcp_code} already exists.")
            
        if obj_in.email:
            existing_email = await self.repository.get_by_email(db, email=obj_in.email)
            if existing_email:
                raise ConflictException(f"HCP with email {obj_in.email} already exists.")
                
        return await super().create(db, obj_in=obj_in)

    async def update(self, db: AsyncSession, *, id: UUID, obj_in: HCPUpdate) -> HCP:
        if obj_in.email:
            existing_email = await self.repository.get_by_email(db, email=obj_in.email)
            if existing_email and str(existing_email.id) != str(id):
                raise ConflictException(f"HCP with email {obj_in.email} already exists.")
        
        return await super().update(db, id=id, obj_in=obj_in)
        
    async def get_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
        specialization: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> tuple[List[HCP], int]:
        return await self.repository.get_paginated(
            db, 
            skip=skip, 
            limit=limit, 
            city=city, 
            specialization=specialization, 
            is_active=is_active, 
            sort_by=sort_by, 
            sort_desc=sort_desc
        )

hcp_service = HCPService(hcp_repository)
