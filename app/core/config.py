"""Application configuration settings using Pydantic Settings."""

from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings for the backend application."""

    PROJECT_NAME: str = "Wird Engine"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database configuration
    # Default: asynchronous SQLite file inside data/wird.db
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/wird.db"

    # Base filesystem paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

    # Tanzil raw source filenames
    TANZIL_UTHMANI_FILE: str = "quran-uthmani.txt"
    TANZIL_SIMPLE_FILE: str = "quran-simple.txt"
    TANZIL_EN_SAHIH_FILE: str = "en.sahih.txt"
    TANZIL_UR_JALANDHRY_FILE: str = "ur.jalandhry.txt"
    SURAH_METADATA_FILE: str = "surah_metadata.json"

    # Tanzil download source URLs
    URL_TANZIL_UTHMANI: str = "https://tanzil.net/pub/download/download.php?quranType=uthmani&outType=txt"
    URL_TANZIL_SIMPLE: str = "https://tanzil.net/pub/download/download.php?quranType=simple-clean&outType=txt"
    URL_TANZIL_EN_SAHIH: str = "https://tanzil.net/trans/en.sahih"
    URL_TANZIL_UR_JALANDHRY: str = "https://tanzil.net/trans/ur.jalandhry"

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # type: ignore
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
