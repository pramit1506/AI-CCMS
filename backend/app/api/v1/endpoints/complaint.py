from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db_session, get_complaint_service
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse
from app.schemas.pagination import PaginatedResponse
from app.shared.responses import APIResponse
from app.shared.enums import ComplaintStatus, ComplaintSource
from app.services.complaint_service import ComplaintService

router = APIRouter()

@router.post("/", response_model=APIResponse[ComplaintResponse], status_code=status.HTTP_201_CREATED)
async def create_complaint(
    complaint_in: ComplaintCreate,
    db: AsyncSession = Depends(get_db_session),
    service: ComplaintService = Depends(get_complaint_service)
) -> APIResponse[ComplaintResponse]:
    complaint = await service.create(db, obj_in=complaint_in)
    return APIResponse(success=True, message="Complaint created successfully", data=ComplaintResponse.model_validate(complaint))

@router.get("/{id}", response_model=APIResponse[ComplaintResponse])
async def get_complaint(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: ComplaintService = Depends(get_complaint_service)
) -> APIResponse[ComplaintResponse]:
    complaint = await service.get_by_id(db, id=id)
    return APIResponse(success=True, message="Complaint retrieved successfully", data=ComplaintResponse.model_validate(complaint))

@router.get("/", response_model=APIResponse[PaginatedResponse[ComplaintResponse]])
async def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    complaint_status: Optional[ComplaintStatus] = Query(None, alias="status"),
    complaint_source: Optional[ComplaintSource] = None,
    sort_by: str = "complaint_date",
    sort_desc: bool = True,
    db: AsyncSession = Depends(get_db_session),
    service: ComplaintService = Depends(get_complaint_service)
) -> APIResponse[PaginatedResponse[ComplaintResponse]]:
    items, total = await service.get_paginated(
        db, skip=skip, limit=limit, customer_id=customer_id, start_date=start_date,
        end_date=end_date, status=complaint_status, complaint_source=complaint_source,
        sort_by=sort_by, sort_desc=sort_desc
    )
    return APIResponse(
        success=True,
        message="Complaints retrieved successfully",
        data=PaginatedResponse(
            items=[ComplaintResponse.model_validate(item) for item in items],
            page=(skip // limit) + 1,
            page_size=limit,
            total=total
        )
    )

@router.put("/{id}", response_model=APIResponse[ComplaintResponse])
async def update_complaint(
    id: UUID,
    complaint_in: ComplaintUpdate,
    db: AsyncSession = Depends(get_db_session),
    service: ComplaintService = Depends(get_complaint_service)
) -> APIResponse[ComplaintResponse]:
    complaint = await service.update(db, id=id, obj_in=complaint_in)
    return APIResponse(success=True, message="Complaint updated successfully", data=ComplaintResponse.model_validate(complaint))

@router.delete("/{id}", response_model=APIResponse[ComplaintResponse])
async def delete_complaint(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: ComplaintService = Depends(get_complaint_service)
) -> APIResponse[ComplaintResponse]:
    complaint = await service.delete(db, id=id)
    return APIResponse(success=True, message="Complaint deleted successfully", data=ComplaintResponse.model_validate(complaint))
