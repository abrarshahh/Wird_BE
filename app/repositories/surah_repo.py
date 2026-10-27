"""Repository for accessing Surah chapter data."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.surah import Surah


class SurahRepository:
    """Async repository handling Surah database queries."""

    @staticmethod
    async def get_all_surahs(session: AsyncSession) -> List[Surah]:
        """Retrieve all 114 Surahs ordered by ID (1 to 114)."""
        stmt = select(Surah).order_by(Surah.id.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_surah_by_id(session: AsyncSession, surah_id: int) -> Optional[Surah]:
        """Retrieve a single Surah by its ID (1 to 114)."""
        stmt = select(Surah).where(Surah.id == surah_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
