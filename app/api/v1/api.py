"""API Version 1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import surahs, ayahs, juz

api_router = APIRouter()

api_router.include_router(surahs.router, prefix="/surahs", tags=["Surahs"])
api_router.include_router(ayahs.router, prefix="/ayahs", tags=["Ayahs"])
api_router.include_router(juz.router, prefix="/juz", tags=["Juz"])
