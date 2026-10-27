"""Ayah ORM Model representing the 6,236 verses of the Quran."""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.surah import Surah
    from app.models.translation import Translation


class Ayah(Base):
    """Ayah model containing both Uthmanic and simplified Arabic text."""

    __tablename__ = "ayahs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=False
    )
    surah_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("surahs.id"), nullable=False, index=True
    )
    ayah_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    text_uthmani: Mapped[str] = mapped_column(Text, nullable=False)
    text_simple: Mapped[str] = mapped_column(Text, nullable=False)
    juz: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    manzil: Mapped[int] = mapped_column(Integer, nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hizb_quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    sajdah: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sajdah_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Constraints & composite indexes
    __table_args__ = (
        UniqueConstraint("surah_id", "ayah_number", name="uq_ayah_surah_number"),
        Index("idx_ayahs_surah_ayah", "surah_id", "ayah_number"),
    )

    # Relationships
    surah: Mapped["Surah"] = relationship("Surah", back_populates="ayahs")
    translations: Mapped[List["Translation"]] = relationship(
        "Translation",
        back_populates="ayah",
        cascade="all, delete-orphan",
        order_by="Translation.language_code",
    )

    def __repr__(self) -> str:
        return f"<Ayah {self.surah_id}:{self.ayah_number}>"
