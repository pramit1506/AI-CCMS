from typing import Generic, TypeVar, Type, Optional, List, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.repositories.base_repository import BaseRepository
from app.database.base import Base
from pydantic import BaseModel
from app.exceptions.base import ResourceNotFoundException

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, repository: BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
        self.repository = repository

    async def get_by_id(self, db: AsyncSession, id: UUID) -> ModelType:
        obj = await self.repository.get_by_id(db, id)
        if not obj:
            logger.warning(f"{self.repository.model.__name__} not found with id: {id}")
            raise ResourceNotFoundException(f"{self.repository.model.__name__} not found")
        return obj

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        try:
            obj = await self.repository.create(db, obj_in=obj_in)
            logger.info(f"Created {self.repository.model.__name__} with id: {obj.id}")
            return obj
        except Exception as e:
            logger.error(f"Error creating {self.repository.model.__name__}: {e}")
            await db.rollback()
            raise

    async def update(self, db: AsyncSession, *, id: UUID, obj_in: UpdateSchemaType) -> ModelType:
        obj = await self.get_by_id(db, id)
        try:
            updated_obj = await self.repository.update(db, db_obj=obj, obj_in=obj_in)
            logger.info(f"Updated {self.repository.model.__name__} with id: {id}")
            return updated_obj
        except Exception as e:
            logger.error(f"Error updating {self.repository.model.__name__} with id {id}: {e}")
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, *, id: UUID) -> ModelType:
        obj = await self.get_by_id(db, id)
        try:
            await self.repository.delete(db, id=id)
            logger.info(f"Deleted {self.repository.model.__name__} with id: {id}")
            return obj
        except Exception as e:
            logger.error(f"Error deleting {self.repository.model.__name__} with id {id}: {e}")
            await db.rollback()
            raise
