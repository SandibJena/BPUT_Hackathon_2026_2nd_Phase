from pydantic_settings import BaseSettings
from pathlib import Path

# Repo root — two levels up from this file (backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> ROOT)
ROOT = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./triage.db"
    ANTHROPIC_API_KEY: str = ""
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENCRYPTION_KEY: str = ""
    DATA_RETENTION_HOURS: int = 24
    RULES_FILE: str = str(ROOT / "data" / "rules" / "red_flags.yaml")
    GLOSSARY_DIR: str = str(ROOT / "data" / "glossary")
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ENVIRONMENT: str = "development"
    DISCLAIMER: str = "Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice."

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Module-level alias for direct import: from app.core.config import DISCLAIMER
DISCLAIMER = settings.DISCLAIMER
