"""Surah ORM Model representing the 114 Surahs of the Quran."""

from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ayah import Ayah
    from app.models.translation import Translation


class Surah(Base):
    """Surah model containing theological metadata for each Quranic chapter."""

    __tablename__ = "surahs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=False
    )
    name_ar: Mapped[str] = mapped_column(String(64), nullable=False)
    name_en: Mapped[str] = mapped_column(String(64), nullable=False)
    name_transliteration: Mapped[str] = mapped_column(String(64), nullable=False)
    revelation_place: Mapped[str] = mapped_column(String(10), nullable=False)
    revelation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    total_ayahs: Mapped[int] = mapped_column(Integer, nullable=False)
    has_bismillah: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    start_juz: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    ayahs: Mapped[List["Ayah"]] = relationship(
        "Ayah",
        back_populates="surah",
        cascade="all, delete-orphan",
        order_by="Ayah.ayah_number",
    )
    translations: Mapped[List["Translation"]] = relationship(
        "Translation",
        back_populates="surah",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Surah {self.id}: {self.name_en} ({self.name_ar})>"
