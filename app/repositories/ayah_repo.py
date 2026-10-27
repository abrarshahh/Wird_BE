"""Repository for accessing Ayah verse data with pre-joined translations."""

from typing import List, Optional, Set
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ayah import Ayah
from app.models.translation import Translation
from app.schemas.ayah import AyahReadingItem


class AyahRepository:
    """Async repository for fetching Ayahs and pre-joining translations with zero N+1 queries."""

    @staticmethod
    async def get_ayahs_by_surah(
        session: AsyncSession,
        surah_id: int,
        languages: Optional[List[str]] = None,
    ) -> List[AyahReadingItem]:
        """Retrieve all Ayahs for a given Surah with pre-joined requested translations."""
        stmt = (
            select(Ayah)
            .where(Ayah.surah_id == surah_id)
            .options(selectinload(Ayah.translations))
            .order_by(Ayah.ayah_number.asc())
        )
        result = await session.execute(stmt)
        ayahs = result.scalars().all()

        target_langs: Set[str] = set(languages or ["en"])
        return [AyahRepository._to_reading_item(a, target_langs) for a in ayahs]

    @staticmethod
    async def get_single_ayah(
        session: AsyncSession,
        surah_id: int,
        ayah_number: int,
        languages: Optional[List[str]] = None,
    ) -> Optional[AyahReadingItem]:
        """Retrieve a single verse by surah_id and ayah_number with requested translations."""
        stmt = (
            select(Ayah)
            .where(Ayah.surah_id == surah_id, Ayah.ayah_number == ayah_number)
            .options(selectinload(Ayah.translations))
        )
        result = await session.execute(stmt)
        ayah = result.scalar_one_or_none()
        if not ayah:
            return None

        target_langs: Set[str] = set(languages or ["en"])
        return AyahRepository._to_reading_item(ayah, target_langs)

    @staticmethod
    async def get_ayahs_by_juz(
        session: AsyncSession,
        juz_number: int,
        languages: Optional[List[str]] = None,
    ) -> List[AyahReadingItem]:
        """Retrieve all Ayahs belonging to a Juz across Surahs with pre-joined translations."""
        stmt = (
            select(Ayah)
            .where(Ayah.juz == juz_number)
            .options(selectinload(Ayah.translations))
            .order_by(Ayah.surah_id.asc(), Ayah.ayah_number.asc())
        )
        result = await session.execute(stmt)
        ayahs = result.scalars().all()

        target_langs: Set[str] = set(languages or ["en"])
        return [AyahRepository._to_reading_item(a, target_langs) for a in ayahs]

    @staticmethod
    def _to_reading_item(ayah: Ayah, target_langs: Set[str]) -> AyahReadingItem:
        """Helper to transform ORM Ayah instance into AyahReadingItem schema."""
        trans_dict = {
            t.language_code: t.text
            for t in ayah.translations
            if t.language_code in target_langs
        }
        return AyahReadingItem(
            id=ayah.id,
            surah_id=ayah.surah_id,
            ayah_number=ayah.ayah_number,
            text_uthmani=ayah.text_uthmani,
            text_simple=ayah.text_simple,
            juz=ayah.juz,
            manzil=ayah.manzil,
            page=ayah.page,
            hizb_quarter=ayah.hizb_quarter,
            sajdah=ayah.sajdah,
            sajdah_type=ayah.sajdah_type,
            translations=trans_dict,
        )
