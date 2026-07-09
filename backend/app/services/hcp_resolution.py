import uuid
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.hcp import HCP
from app.schemas.hcp import HCPCreate
from app.services.hcp_service import hcp_service
from app.repositories.hcp_repository import hcp_repository
from app.core.config import settings
from loguru import logger

class HCPResolutionService:
    async def resolve_hcp(self, db: AsyncSession, hcp_name: Optional[str] = None, hcp_id: Optional[str] = None) -> Tuple[Optional[HCP], Optional[str]]:
        """
        Attempts to resolve an HCP by ID or name.
        If not found by name and auto-create is enabled, creates a new HCP.
        Returns a tuple of (HCP object, Error Message).
        """
        if hcp_id:
            try:
                hcp = await hcp_service.get_by_id(db, id=uuid.UUID(hcp_id))
                if hcp:
                    return hcp, None
            except ValueError:
                pass # Not a UUID; try the business HCP code next.

            hcp = await hcp_repository.get_by_hcp_code(db, hcp_id)
            if hcp:
                return hcp, None

        if hcp_name:
            # Simple lookup logic for now: search by first or last name
            name_parts = hcp_name.strip().split()
            last_name = name_parts[-1]
            first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else ""

            # Try to find by name
            query = select(HCP).where(HCP.last_name.ilike(f"%{last_name}%"))
            result = await db.execute(query)
            existing_hcp = result.scalars().first()
            
            if existing_hcp:
                logger.info(f"Resolved HCP by name '{hcp_name}' to ID: {existing_hcp.id}")
                return existing_hcp, None

            # Auto-create if enabled
            auto_create_enabled = getattr(settings, "AUTO_CREATE_HCP", True)

            if auto_create_enabled:
                hcp_code = f"HCP-{uuid.uuid4().hex[:8].upper()}"
                new_hcp_data = HCPCreate(
                    hcp_code=hcp_code,
                    first_name=first_name or hcp_name,
                    last_name=last_name or hcp_name,
                    is_active=True
                )
                logger.info(f"Auto-creating new HCP: {new_hcp_data.model_dump()}")
                created_hcp = await hcp_service.create(db, obj_in=new_hcp_data)
                return created_hcp, None
            else:
                return None, f"HCP '{hcp_name}' not found and auto-create is disabled."
                
        return None, "No HCP name or ID provided."

hcp_resolution_service = HCPResolutionService()
