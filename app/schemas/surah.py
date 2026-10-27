"""Pydantic V2 schemas for Surah metadata and full reading views."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.ayah import AyahReadingItem


class SurahListItem(BaseModel):
    """Surah chapter metadata for listings and navigation."""

    id: int = Field(..., description="Surah number (1 to 114)")
    name_ar: str = Field(..., description="Arabic name (e.g. 'الفاتحة')")
    name_en: str = Field(..., description="English transliteration (e.g. 'Al-Fatihah')")
    name_transliteration: str = Field(..., description="English meaning of the title (e.g. 'The Opening')")
    revelation_place: str = Field(..., description="Place of revelation ('makkah' or 'madinah')")
    revelation_order: int = Field(..., description="Chronological revelation order (1 to 114)")
    total_ayahs: int = Field(..., description="Total verse count in the Surah")
    has_bismillah: bool = Field(
        ...,
        description="Whether Surah header includes Bismillah (False only for Surah 9)"
    )
    start_page: int = Field(..., description="Starting Medina Mushaf page number (1 to 604)")
    start_juz: int = Field(..., description="Starting Juz number (1 to 30)")

    model_config = ConfigDict(from_attributes=True)


class SurahReadingResponse(BaseModel):
    """Comprehensive Surah reading payload containing chapter metadata and all verses."""

    surah: SurahListItem = Field(..., description="Surah chapter metadata")
    total_ayahs: int = Field(..., description="Count of ayahs returned in payload")
    ayahs: List[AyahReadingItem] = Field(
        ...,
        description="Ordered list of verse objects with requested translations"
    )

    model_config = ConfigDict(from_attributes=True)
