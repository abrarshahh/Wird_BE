"""API endpoints for Surah catalog and reading views."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.surah import SurahListItem, SurahReadingResponse
from app.services.quran_service import QuranService

router = APIRouter()


def parse_languages(translations: Optional[str]) -> List[str]:
    """Parse comma-separated translation language string."""
    if not translations:
        return ["en"]
    langs = [lang.strip().lower() for lang in translations.split(",") if lang.strip()]
    return langs if langs else ["en"]


@router.get(
    "",
    response_model=List[SurahListItem],
    summary="List all Surahs",
    description="Retrieve metadata for all 114 Surahs ordered by chapter number.",
)
async def list_surahs(
    db: AsyncSession = Depends(get_db),
) -> List[SurahListItem]:
    """Return all 114 Surahs from in-memory cache with database fallback."""
    return await QuranService.get_surah_list(session=db)


@router.get(
    "/{id}",
    response_model=SurahReadingResponse,
    summary="Get Surah Reading View",
    description="Retrieve full reading payload for a Surah with ordered verses and requested translations.",
)
async def get_surah_reading(
    id: int,
    translations: Optional[str] = Query(
        default="en",
        description="Comma-separated language codes for translations (e.g. 'en', 'ur', 'en,ur')",
        examples=["en", "en,ur"],
    ),
    db: AsyncSession = Depends(get_db),
) -> SurahReadingResponse:
    """Return full Surah reading view."""
    if id < 1 or id > 114:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surah with ID {id} not found. Must be between 1 and 114.",
        )

    langs = parse_languages(translations)
    response = await QuranService.get_surah_reading(
        surah_id=id, languages=langs, session=db
    )
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surah with ID {id} not found.",
        )
    return response
