"""API endpoints for single Ayah lookup."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.ayah import AyahReadingItem
from app.services.quran_service import QuranService

router = APIRouter()


def parse_languages(translations: Optional[str]) -> List[str]:
    """Parse comma-separated translation language string."""
    if not translations:
        return ["en"]
    langs = [lang.strip().lower() for lang in translations.split(",") if lang.strip()]
    return langs if langs else ["en"]


@router.get(
    "/{surah_id}/{ayah_number}",
    response_model=AyahReadingItem,
    summary="Get single Ayah detail",
    description="Retrieve a specific verse by Surah number and Ayah number with requested translations.",
)
async def get_ayah(
    surah_id: int,
    ayah_number: int,
    translations: Optional[str] = Query(
        default="en",
        description="Comma-separated language codes for translations (e.g. 'en', 'ur')",
    ),
    db: AsyncSession = Depends(get_db),
) -> AyahReadingItem:
    """Return a single Ayah reading item."""
    if surah_id < 1 or surah_id > 114:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surah with ID {surah_id} not found. Must be between 1 and 114.",
        )

    langs = parse_languages(translations)
    ayah = await QuranService.get_ayah_detail(
        surah_id=surah_id, ayah_number=ayah_number, languages=langs, session=db
    )
    if not ayah:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ayah {surah_id}:{ayah_number} not found.",
        )
    return ayah
