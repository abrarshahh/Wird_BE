"""Pydantic V2 schemas for Ayah representations and translations."""

from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class TranslationItem(BaseModel):
    """Single translation record schema."""

    language_code: str = Field(..., description="ISO 639-1 language code (e.g. 'en', 'ur')")
    translator_id: str = Field(..., description="Unique translator identifier (e.g. 'sahih')")
    text: str = Field(..., description="Translated verse text")

    model_config = ConfigDict(from_attributes=True)


class AyahReadingItem(BaseModel):
    """Verse payload optimized for reading interfaces."""

    id: int = Field(..., description="Global sequential Ayah ID (1 to 6236)")
    surah_id: int = Field(..., description="Surah number (1 to 114)")
    ayah_number: int = Field(..., description="Verse number within the Surah")
    text_uthmani: str = Field(..., description="Authentic Uthmanic Medina Mushaf text with diacritics")
    text_simple: str = Field(..., description="Clean Arabic text without diacritics")
    juz: int = Field(..., description="Juz number (1 to 30)")
    manzil: int = Field(..., description="Manzil number (1 to 7)")
    page: int = Field(..., description="Medina Mushaf page number (1 to 604)")
    hizb_quarter: int = Field(..., description="Hizb quarter index (1 to 240)")
    sajdah: bool = Field(..., description="Whether this verse contains a prostration")
    sajdah_type: Optional[str] = Field(None, description="Prostration type ('recommended' or 'obligatory')")
    translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of language_code to translated text (e.g. {'en': '...', 'ur': '...'})"
    )

    model_config = ConfigDict(from_attributes=True)
