"""Translation ORM Model storing multi-language translations of each Ayah."""

from typing import TYPE_CHECKING
from sqlalchemy import (
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
    from app.models.ayah import Ayah
    from app.models.surah import Surah


class Translation(Base):
    """Translation model storing translated verse text per language and translator."""

    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ayah_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ayahs.id"), nullable=False, index=True
    )
    surah_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("surahs.id"), nullable=False, index=True
    )
    ayah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    language_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    translator_id: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint(
            "ayah_id",
            "language_code",
            "translator_id",
            name="uq_translation_ayah_lang_translator",
        ),
        Index("idx_translations_lookup", "surah_id", "language_code"),
    )

    # Relationships
    ayah: Mapped["Ayah"] = relationship("Ayah", back_populates="translations")
    surah: Mapped["Surah"] = relationship("Surah", back_populates="translations")

    def __repr__(self) -> str:
        return f"<Translation {self.surah_id}:{self.ayah_number} [{self.language_code}:{self.translator_id}]>"
