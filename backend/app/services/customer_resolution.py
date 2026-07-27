import uuid
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate
from app.services.customer_service import customer_service
from app.repositories.customer_repository import customer_repository
from app.core.config import settings
from loguru import logger

class CustomerResolutionService:
    async def resolve_customer(self, db: AsyncSession, customer_name: Optional[str] = None, customer_id: Optional[str] = None) -> Tuple[Optional[Customer], Optional[str]]:
        if customer_id:
            try:
                cust = await customer_service.get_by_id(db, id=uuid.UUID(customer_id))
                if cust:
                    return cust, None
            except ValueError:
                pass 

            cust = await customer_repository.get_by_customer_code(db, customer_id)
            if cust:
                return cust, None

        if customer_name:
            query = select(Customer).where(Customer.customer_name.ilike(f"%{customer_name}%"))
            result = await db.execute(query)
            existing_cust = result.scalars().first()
            
            if existing_cust:
                logger.info(f"Resolved Customer by name '{customer_name}' to ID: {existing_cust.id}")
                return existing_cust, None

            auto_create_enabled = getattr(settings, "AUTO_CREATE_CUSTOMER", True)

            if auto_create_enabled:
                customer_code = f"CUST-{uuid.uuid4().hex[:8].upper()}"
                new_cust_data = CustomerCreate(
                    customer_code=customer_code,
                    customer_name=customer_name,
                    is_active=True
                )
                logger.info(f"Auto-creating new Customer: {new_cust_data.model_dump()}")
                created_cust = await customer_service.create(db, obj_in=new_cust_data)
                return created_cust, None
            else:
                return None, f"Customer '{customer_name}' not found and auto-create is disabled."
                
        return None, "No Customer name or ID provided."

customer_resolution_service = CustomerResolutionService()
