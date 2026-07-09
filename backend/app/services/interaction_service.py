from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseService
from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.repositories.interaction_repository import interaction_repository
from app.repositories.hcp_repository import hcp_repository
from app.exceptions.base import BusinessRuleException, ConflictException, ResourceNotFoundException
from app.shared.enums import InteractionStatus, InteractionType

class InteractionService(BaseService[Interaction, InteractionCreate, InteractionUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: InteractionCreate) -> Interaction:
        existing_interaction = await self.repository.get_by_interaction_number(db, interaction_number=obj_in.interaction_number)
        if existing_interaction:
            raise ConflictException(f"Interaction with number {obj_in.interaction_number} already exists.")
            
        hcp = await hcp_repository.get_by_id(db, id=obj_in.hcp_id)
        if not hcp:
            raise ResourceNotFoundException(f"HCP with id {obj_in.hcp_id} not found.")

        self._validate_business_rules(obj_in)
                
        return await super().create(db, obj_in=obj_in)

    async def update(self, db: AsyncSession, *, id: UUID, obj_in: InteractionUpdate) -> Interaction:
        existing_interaction = await self.get_by_id(db, id)
        
        self._validate_status_transition(existing_interaction.status, obj_in.status)
        self._validate_business_rules_update(existing_interaction, obj_in)
        
        return await super().update(db, id=id, obj_in=obj_in)
        
    def _validate_business_rules(self, obj_in: InteractionCreate):
        if obj_in.follow_up_date and obj_in.interaction_date:
            if obj_in.follow_up_date < obj_in.interaction_date:
                raise BusinessRuleException("Follow-up date cannot precede interaction date.")
                
        if obj_in.status == InteractionStatus.COMPLETED and not obj_in.discussion_summary:
            raise BusinessRuleException("Discussion summary is required when status is COMPLETED.")

    def _validate_business_rules_update(self, existing: Interaction, obj_in: InteractionUpdate):
        interaction_date = obj_in.interaction_date if obj_in.interaction_date is not None else existing.interaction_date
        follow_up_date = obj_in.follow_up_date if obj_in.follow_up_date is not None else existing.follow_up_date
        status = obj_in.status if obj_in.status is not None else existing.status
        discussion_summary = obj_in.discussion_summary if obj_in.discussion_summary is not None else existing.discussion_summary
        
        if follow_up_date and interaction_date:
            if follow_up_date < interaction_date:
                raise BusinessRuleException("Follow-up date cannot precede interaction date.")
                
        if status == InteractionStatus.COMPLETED and not discussion_summary:
            raise BusinessRuleException("Discussion summary is required when status is COMPLETED.")
            
    def _validate_status_transition(self, current_status: InteractionStatus, new_status: Optional[InteractionStatus]):
        if not new_status or current_status == new_status:
            return
            
        valid_transitions = {
            InteractionStatus.PLANNED: [InteractionStatus.COMPLETED, InteractionStatus.CANCELLED, InteractionStatus.NO_SHOW],
            InteractionStatus.COMPLETED: [],
            InteractionStatus.CANCELLED: [],
            InteractionStatus.NO_SHOW: [InteractionStatus.PLANNED, InteractionStatus.COMPLETED, InteractionStatus.CANCELLED]
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise BusinessRuleException(f"Invalid status transition from {current_status} to {new_status}")

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
        return await self.repository.get_paginated(
            db, 
            skip=skip, 
            limit=limit, 
            hcp_id=hcp_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            interaction_type=interaction_type,
            sort_by=sort_by, 
            sort_desc=sort_desc
        )

interaction_service = InteractionService(interaction_repository)
