"""API endpoints for Juz (Para) catalog and reading views."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.juz import JuzSummary, JuzReadingResponse
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
    response_model=List[JuzSummary],
    summary="List all 30 Juzs",
    description="Retrieve summary boundaries for all 30 Juzs.",
)
async def list_juzs(
    db: AsyncSession = Depends(get_db),
) -> List[JuzSummary]:
    """Return list of all 30 Juzs."""
    return await QuranService.get_juz_list(session=db)


@router.get(
    "/{id}",
    response_model=JuzReadingResponse,
    summary="Get Juz Reading View",
    description="Retrieve full reading view for a specific Juz (1 to 30) across Surah boundaries.",
)
async def get_juz_reading(
    id: int,
    translations: Optional[str] = Query(
        default="en",
        description="Comma-separated language codes for translations (e.g. 'en', 'ur')",
    ),
    db: AsyncSession = Depends(get_db),
) -> JuzReadingResponse:
    """Return full reading view for a Juz."""
    if id < 1 or id > 30:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juz number {id} not found. Must be between 1 and 30.",
        )

    langs = parse_languages(translations)
    response = await QuranService.get_juz_reading(
        juz_number=id, languages=langs, session=db
    )
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juz number {id} not found.",
        )
    return response
