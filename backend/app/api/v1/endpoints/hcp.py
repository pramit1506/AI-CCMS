from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db_session, get_hcp_service
from app.schemas.hcp import HCPCreate, HCPUpdate, HCPResponse
from app.schemas.pagination import PaginatedResponse
from app.shared.responses import APIResponse
from app.services.hcp_service import HCPService

router = APIRouter()

@router.post("/", response_model=APIResponse[HCPResponse], status_code=status.HTTP_201_CREATED)
async def create_hcp(
    hcp_in: HCPCreate,
    db: AsyncSession = Depends(get_db_session),
    service: HCPService = Depends(get_hcp_service)
) -> APIResponse[HCPResponse]:
    hcp = await service.create(db, obj_in=hcp_in)
    return APIResponse(success=True, message="HCP created successfully", data=HCPResponse.model_validate(hcp))

@router.get("/{id}", response_model=APIResponse[HCPResponse])
async def get_hcp(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: HCPService = Depends(get_hcp_service)
) -> APIResponse[HCPResponse]:
    hcp = await service.get_by_id(db, id=id)
    return APIResponse(success=True, message="HCP retrieved successfully", data=HCPResponse.model_validate(hcp))

@router.get("/", response_model=APIResponse[PaginatedResponse[HCPResponse]])
async def list_hcps(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    specialization: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
    db: AsyncSession = Depends(get_db_session),
    service: HCPService = Depends(get_hcp_service)
) -> APIResponse[PaginatedResponse[HCPResponse]]:
    items, total = await service.get_paginated(
        db, skip=skip, limit=limit, city=city, specialization=specialization,
        is_active=is_active, sort_by=sort_by, sort_desc=sort_desc
    )
    return APIResponse(
        success=True,
        message="HCPs retrieved successfully",
        data=PaginatedResponse(
            items=[HCPResponse.model_validate(item) for item in items],
            page=(skip // limit) + 1,
            page_size=limit,
            total=total
        )
    )

@router.put("/{id}", response_model=APIResponse[HCPResponse])
async def update_hcp(
    id: UUID,
    hcp_in: HCPUpdate,
    db: AsyncSession = Depends(get_db_session),
    service: HCPService = Depends(get_hcp_service)
) -> APIResponse[HCPResponse]:
    hcp = await service.update(db, id=id, obj_in=hcp_in)
    return APIResponse(success=True, message="HCP updated successfully", data=HCPResponse.model_validate(hcp))

@router.delete("/{id}", response_model=APIResponse[HCPResponse])
async def delete_hcp(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: HCPService = Depends(get_hcp_service)
) -> APIResponse[HCPResponse]:
    hcp = await service.delete(db, id=id)
    return APIResponse(success=True, message="HCP deleted successfully", data=HCPResponse.model_validate(hcp))
