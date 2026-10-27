"""High-performance in-memory caching and Quran domain service layer.

Provides sub-millisecond serving for:
- Surah catalog listing
- Surah reading view (verses + selected translations)
- Single Ayah detail
- Juz catalog listing & Juz reading views

Pre-warms all immutable Quran data into memory on startup.
"""

from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.surah import Surah
from app.repositories.surah_repo import SurahRepository
from app.repositories.ayah_repo import AyahRepository
from app.schemas.surah import SurahListItem, SurahReadingResponse
from app.schemas.ayah import AyahReadingItem
from app.schemas.juz import JuzSummary, JuzReadingResponse


class QuranService:
    """Singleton in-memory cache and service layer for Quran content."""

    _is_warmed: bool = False
    _surahs_list: List[SurahListItem] = []
    _surahs_map: Dict[int, SurahListItem] = {}
    _ayahs_by_surah: Dict[int, List[AyahReadingItem]] = {}
    _ayahs_by_key: Dict[Tuple[int, int], AyahReadingItem] = {}
    _juz_summaries: List[JuzSummary] = []
    _ayahs_by_juz: Dict[int, List[AyahReadingItem]] = {}

    @classmethod
    async def warm_cache(cls, session: AsyncSession) -> None:
        """Pre-load and index all Surahs, Ayahs, and Translations into RAM."""
        # 1. Load all 114 Surahs
        db_surahs = await SurahRepository.get_all_surahs(session)
        cls._surahs_list = [SurahListItem.model_validate(s) for s in db_surahs]
        cls._surahs_map = {s.id: s for s in cls._surahs_list}

        # 2. Load all 6,236 Ayahs with all available translations ('en', 'ur')
        all_langs = ["en", "ur"]
        cls._ayahs_by_surah.clear()
        cls._ayahs_by_key.clear()
        cls._ayahs_by_juz = {j: [] for j in range(1, 31)}

        for surah in cls._surahs_list:
            ayahs = await AyahRepository.get_ayahs_by_surah(session, surah.id, all_langs)
            cls._ayahs_by_surah[surah.id] = ayahs
            for a in ayahs:
                cls._ayahs_by_key[(a.surah_id, a.ayah_number)] = a
                cls._ayahs_by_juz[a.juz].append(a)

        # 3. Build Juz Summaries (1 to 30)
        cls._juz_summaries = []
        for j_num in range(1, 31):
            j_ayahs = cls._ayahs_by_juz[j_num]
            if j_ayahs:
                cls._juz_summaries.append(
                    JuzSummary(
                        juz_number=j_num,
                        start_surah=j_ayahs[0].surah_id,
                        start_ayah=j_ayahs[0].ayah_number,
                        total_ayahs=len(j_ayahs),
                    )
                )

        cls._is_warmed = True

    @classmethod
    def is_warmed(cls) -> bool:
        """Check if in-memory cache is ready."""
        return cls._is_warmed

    @classmethod
    async def get_surah_list(cls, session: Optional[AsyncSession] = None) -> List[SurahListItem]:
        """Return all 114 Surahs. Serves from RAM if warmed, else falls back to DB."""
        if cls._is_warmed:
            return cls._surahs_list
        if session:
            db_surahs = await SurahRepository.get_all_surahs(session)
            return [SurahListItem.model_validate(s) for s in db_surahs]
        return []

    @classmethod
    async def get_surah_by_id(
        cls, surah_id: int, session: Optional[AsyncSession] = None
    ) -> Optional[SurahListItem]:
        """Return Surah metadata by ID."""
        if cls._is_warmed:
            return cls._surahs_map.get(surah_id)
        if session:
            db_surah = await SurahRepository.get_surah_by_id(session, surah_id)
            return SurahListItem.model_validate(db_surah) if db_surah else None
        return None

    @classmethod
    async def get_surah_reading(
        cls,
        surah_id: int,
        languages: Optional[List[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[SurahReadingResponse]:
        """Return full reading payload for a Surah with selective translation filtering."""
        target_langs = set(languages or ["en"])

        if cls._is_warmed:
            surah = cls._surahs_map.get(surah_id)
            if not surah:
                return None
            cached_ayahs = cls._ayahs_by_surah.get(surah_id, [])
            filtered_ayahs = [
                cls._filter_translations(a, target_langs) for a in cached_ayahs
            ]
            return SurahReadingResponse(
                surah=surah,
                total_ayahs=len(filtered_ayahs),
                ayahs=filtered_ayahs,
            )

        if session:
            db_surah = await SurahRepository.get_surah_by_id(session, surah_id)
            if not db_surah:
                return None
            surah_item = SurahListItem.model_validate(db_surah)
            ayahs = await AyahRepository.get_ayahs_by_surah(session, surah_id, list(target_langs))
            return SurahReadingResponse(
                surah=surah_item,
                total_ayahs=len(ayahs),
                ayahs=ayahs,
            )
        return None

    @classmethod
    async def get_ayah_detail(
        cls,
        surah_id: int,
        ayah_number: int,
        languages: Optional[List[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[AyahReadingItem]:
        """Return single Ayah with requested translations."""
        target_langs = set(languages or ["en"])

        if cls._is_warmed:
            ayah = cls._ayahs_by_key.get((surah_id, ayah_number))
            if not ayah:
                return None
            return cls._filter_translations(ayah, target_langs)

        if session:
            return await AyahRepository.get_single_ayah(
                session, surah_id, ayah_number, list(target_langs)
            )
        return None

    @classmethod
    async def get_juz_list(cls, session: Optional[AsyncSession] = None) -> List[JuzSummary]:
        """Return list of all 30 Juz summaries."""
        if cls._is_warmed:
            return cls._juz_summaries
        return []

    @classmethod
    async def get_juz_reading(
        cls,
        juz_number: int,
        languages: Optional[List[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[JuzReadingResponse]:
        """Return reading payload for an entire Juz with constituent verses."""
        if juz_number < 1 or juz_number > 30:
            return None

        target_langs = set(languages or ["en"])

        if cls._is_warmed:
            cached_ayahs = cls._ayahs_by_juz.get(juz_number, [])
            if not cached_ayahs:
                return None
            summary = next((j for j in cls._juz_summaries if j.juz_number == juz_number), None)
            if not summary:
                return None
            filtered_ayahs = [
                cls._filter_translations(a, target_langs) for a in cached_ayahs
            ]
            return JuzReadingResponse(
                juz=summary,
                total_ayahs=len(filtered_ayahs),
                ayahs=filtered_ayahs,
            )

        if session:
            ayahs = await AyahRepository.get_ayahs_by_juz(session, juz_number, list(target_langs))
            if not ayahs:
                return None
            summary = JuzSummary(
                juz_number=juz_number,
                start_surah=ayahs[0].surah_id,
                start_ayah=ayahs[0].ayah_number,
                total_ayahs=len(ayahs),
            )
            return JuzReadingResponse(
                juz=summary,
                total_ayahs=len(ayahs),
                ayahs=ayahs,
            )
        return None

    @staticmethod
    def _filter_translations(ayah: AyahReadingItem, target_langs: Set[str]) -> AyahReadingItem:
        """Create a copy of AyahReadingItem with translations limited to target_langs."""
        filtered_trans = {
            lang: text for lang, text in ayah.translations.items() if lang in target_langs
        }
        return ayah.model_copy(update={"translations": filtered_trans})
