from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db_session, get_customer_service
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.pagination import PaginatedResponse
from app.shared.responses import APIResponse
from app.services.customer_service import CustomerService

router = APIRouter()

@router.post("/", response_model=APIResponse[CustomerResponse], status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    db: AsyncSession = Depends(get_db_session),
    service: CustomerService = Depends(get_customer_service)
) -> APIResponse[CustomerResponse]:
    customer = await service.create(db, obj_in=customer_in)
    return APIResponse(success=True, message="Customer created successfully", data=CustomerResponse.model_validate(customer))

@router.get("/{id}", response_model=APIResponse[CustomerResponse])
async def get_customer(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: CustomerService = Depends(get_customer_service)
) -> APIResponse[CustomerResponse]:
    customer = await service.get_by_id(db, id=id)
    return APIResponse(success=True, message="Customer retrieved successfully", data=CustomerResponse.model_validate(customer))

@router.get("/", response_model=APIResponse[PaginatedResponse[CustomerResponse]])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
    db: AsyncSession = Depends(get_db_session),
    service: CustomerService = Depends(get_customer_service)
) -> APIResponse[PaginatedResponse[CustomerResponse]]:
    items, total = await service.get_paginated(
        db, skip=skip, limit=limit, city=city,
        is_active=is_active, sort_by=sort_by, sort_desc=sort_desc
    )
    return APIResponse(
        success=True,
        message="Customers retrieved successfully",
        data=PaginatedResponse(
            items=[CustomerResponse.model_validate(item) for item in items],
            page=(skip // limit) + 1,
            page_size=limit,
            total=total
        )
    )

@router.put("/{id}", response_model=APIResponse[CustomerResponse])
async def update_customer(
    id: UUID,
    customer_in: CustomerUpdate,
    db: AsyncSession = Depends(get_db_session),
    service: CustomerService = Depends(get_customer_service)
) -> APIResponse[CustomerResponse]:
    customer = await service.update(db, id=id, obj_in=customer_in)
    return APIResponse(success=True, message="Customer updated successfully", data=CustomerResponse.model_validate(customer))

@router.delete("/{id}", response_model=APIResponse[CustomerResponse])
async def delete_customer(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    service: CustomerService = Depends(get_customer_service)
) -> APIResponse[CustomerResponse]:
    customer = await service.delete(db, id=id)
    return APIResponse(success=True, message="Customer deleted successfully", data=CustomerResponse.model_validate(customer))
