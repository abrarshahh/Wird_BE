"""Database models package exporting Base and all domain models."""

from app.core.database import Base
from app.models.surah import Surah
from app.models.ayah import Ayah
from app.models.translation import Translation

__all__ = ["Base", "Surah", "Ayah", "Translation"]
