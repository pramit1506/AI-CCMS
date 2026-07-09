from typing import Optional, List
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.models.hcp import HCP
from app.schemas.hcp import HCPCreate, HCPUpdate

class RepositoryHCP(BaseRepository[HCP, HCPCreate, HCPUpdate]):
    async def get_by_hcp_code(self, db: AsyncSession, hcp_code: str) -> Optional[HCP]:
        query = select(self.model).where(self.model.hcp_code == hcp_code)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[HCP]:
        query = select(self.model).where(self.model.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

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
        query = select(self.model)
        
        if city:
            query = query.where(self.model.city.ilike(f"%{city}%"))
        if specialization:
            query = query.where(self.model.specialization.ilike(f"%{specialization}%"))
        if is_active is not None:
            query = query.where(self.model.is_active == is_active)
            
        sort_column = getattr(self.model, sort_by, self.model.created_at)
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

hcp_repository = RepositoryHCP(HCP)
