from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseService
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.repositories.customer_repository import customer_repository
from app.exceptions.base import ConflictException

class CustomerService(BaseService[Customer, CustomerCreate, CustomerUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: CustomerCreate) -> Customer:
        existing_customer = await self.repository.get_by_customer_code(db, customer_code=obj_in.customer_code)
        if existing_customer:
            raise ConflictException(f"Customer with code {obj_in.customer_code} already exists.")
            
        if obj_in.email:
            existing_email = await self.repository.get_by_email(db, email=obj_in.email)
            if existing_email:
                raise ConflictException(f"Customer with email {obj_in.email} already exists.")
                
        return await super().create(db, obj_in=obj_in)

    async def update(self, db: AsyncSession, *, id: UUID, obj_in: CustomerUpdate) -> Customer:
        if obj_in.email:
            existing_email = await self.repository.get_by_email(db, email=obj_in.email)
            if existing_email and str(existing_email.id) != str(id):
                raise ConflictException(f"Customer with email {obj_in.email} already exists.")
        
        return await super().update(db, id=id, obj_in=obj_in)
        
    async def get_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> tuple[List[Customer], int]:
        return await self.repository.get_paginated(
            db, 
            skip=skip, 
            limit=limit, 
            city=city, 
            is_active=is_active, 
            sort_by=sort_by, 
            sort_desc=sort_desc
        )

customer_service = CustomerService(customer_repository)
