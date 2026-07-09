from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db_session, get_interaction_service
from app.schemas.interaction import InteractionCreate, InteractionUpdate, InteractionResponse
from app.schemas.pagination import PaginatedResponse
from app.shared.responses import APIResponse
from app.shared.enums import InteractionStatus, InteractionType
from app.services.interaction_service import InteractionService

router = APIRouter()

@router.post("/", response_model=APIResponse[InteractionResponse], status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction_in: InteractionCreate,
    db: AsyncSession = Depends(get_db_session),
    service: InteractionService = Depends(get_interaction_service)
) -> APIResponse[InteractionResponse]:
    interaction = await service.create(db, obj_in=interaction_in)
    return APIResponse(success=True, message="Interaction created successfully", data=InteractionResponse.model_validate(interaction))

@router.get("/{id}", response_model=APIResponse[InteractionResponse])
async def get_interaction(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: InteractionService = Depends(get_interaction_service)
) -> APIResponse[InteractionResponse]:
    interaction = await service.get_by_id(db, id=id)
    return APIResponse(success=True, message="Interaction retrieved successfully", data=InteractionResponse.model_validate(interaction))

@router.get("/", response_model=APIResponse[PaginatedResponse[InteractionResponse]])
async def list_interactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    hcp_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    interaction_status: Optional[InteractionStatus] = Query(None, alias="status"),
    interaction_type: Optional[InteractionType] = None,
    sort_by: str = "interaction_date",
    sort_desc: bool = True,
    db: AsyncSession = Depends(get_db_session),
    service: InteractionService = Depends(get_interaction_service)
) -> APIResponse[PaginatedResponse[InteractionResponse]]:
    items, total = await service.get_paginated(
        db, skip=skip, limit=limit, hcp_id=hcp_id, start_date=start_date,
        end_date=end_date, status=interaction_status, interaction_type=interaction_type,
        sort_by=sort_by, sort_desc=sort_desc
    )
    return APIResponse(
        success=True,
        message="Interactions retrieved successfully",
        data=PaginatedResponse(
            items=[InteractionResponse.model_validate(item) for item in items],
            page=(skip // limit) + 1,
            page_size=limit,
            total=total
        )
    )

@router.put("/{id}", response_model=APIResponse[InteractionResponse])
async def update_interaction(
    id: UUID,
    interaction_in: InteractionUpdate,
    db: AsyncSession = Depends(get_db_session),
    service: InteractionService = Depends(get_interaction_service)
) -> APIResponse[InteractionResponse]:
    interaction = await service.update(db, id=id, obj_in=interaction_in)
    return APIResponse(success=True, message="Interaction updated successfully", data=InteractionResponse.model_validate(interaction))

@router.delete("/{id}", response_model=APIResponse[InteractionResponse])
async def delete_interaction(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: InteractionService = Depends(get_interaction_service)
) -> APIResponse[InteractionResponse]:
    interaction = await service.delete(db, id=id)
    return APIResponse(success=True, message="Interaction deleted successfully", data=InteractionResponse.model_validate(interaction))
