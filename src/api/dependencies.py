"""FastAPI dependencies."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
