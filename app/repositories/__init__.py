"""Repositories package exporting data access classes."""

from app.repositories.surah_repo import SurahRepository
from app.repositories.ayah_repo import AyahRepository

__all__ = ["SurahRepository", "AyahRepository"]
