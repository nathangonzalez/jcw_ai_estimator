from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

def _csv(s: Optional[str], default: Optional[List[str]] = None) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()] or (default or [])

class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    ENABLE_DEBUG_ROUTES: bool = os.getenv("ENABLE_DEBUG_ROUTES", "true").lower() == "true"

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = _csv(
        os.getenv("CORS_ALLOW_ORIGINS"),
        ["http://localhost:3000"]
    )

    # Storage
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # "local" | "gcs"
    LOCAL_FILES_DIR: str = os.getenv("LOCAL_FILES_DIR", "/tmp/jcw/uploads")  # Cloud Run writable

    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Uploads
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))
    ALLOWED_EXTENSIONS: List[str] = _csv(
        os.getenv("ALLOWED_EXTENSIONS"),
        [".pdf", ".dwg", ".dxf", ".png", ".jpg", ".jpeg"]
    )

    # GCS
    GCS_BUCKET: Optional[str] = os.getenv("GCS_BUCKET")

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

settings = Settings()
