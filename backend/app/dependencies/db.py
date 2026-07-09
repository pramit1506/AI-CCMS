from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import async_session_maker

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session.
    """
    async with async_session_maker() as session:
        yield session
