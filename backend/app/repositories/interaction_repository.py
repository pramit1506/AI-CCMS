from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.shared.enums import InteractionStatus, InteractionType

class RepositoryInteraction(BaseRepository[Interaction, InteractionCreate, InteractionUpdate]):
    async def get_by_interaction_number(self, db: AsyncSession, interaction_number: str) -> Optional[Interaction]:
        query = select(self.model).where(self.model.interaction_number == interaction_number)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        hcp_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[InteractionStatus] = None,
        interaction_type: Optional[InteractionType] = None,
        sort_by: str = "interaction_date",
        sort_desc: bool = True
    ) -> tuple[List[Interaction], int]:
        query = select(self.model)
        
        if hcp_id:
            query = query.where(self.model.hcp_id == hcp_id)
        if start_date:
            query = query.where(self.model.interaction_date >= start_date)
        if end_date:
            query = query.where(self.model.interaction_date <= end_date)
        if status:
            query = query.where(self.model.status == status)
        if interaction_type:
            query = query.where(self.model.interaction_type == interaction_type)
            
        sort_column = getattr(self.model, sort_by, self.model.interaction_date)
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

interaction_repository = RepositoryInteraction(Interaction)
