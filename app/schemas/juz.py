"""Pydantic V2 schemas for Juz (Para) reading views."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.ayah import AyahReadingItem


class JuzSummary(BaseModel):
    """Juz summary metadata."""

    juz_number: int = Field(..., description="Juz number (1 to 30)")
    start_surah: int = Field(..., description="Surah ID of the first verse in the Juz")
    start_ayah: int = Field(..., description="Ayah number of the first verse in the Juz")
    total_ayahs: int = Field(..., description="Total verses contained within the Juz")

    model_config = ConfigDict(from_attributes=True)


class JuzReadingResponse(BaseModel):
    """Juz reading payload containing boundary summary and all constituent verses."""

    juz: JuzSummary = Field(..., description="Juz summary metadata")
    total_ayahs: int = Field(..., description="Count of ayahs returned in payload")
    ayahs: List[AyahReadingItem] = Field(
        ...,
        description="Ordered list of verses within this Juz across Surahs"
    )

    model_config = ConfigDict(from_attributes=True)
