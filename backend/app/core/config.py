from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
DISCLAIMER = (
    'Educational prototype for triage support only. This system provides '
    'decision-support information only. It does not diagnose, prescribe '
    'treatment, or replace a qualified healthcare professional.'
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    app_env: Literal['development', 'test'] = 'development'
    database_url: str = ''
    frontend_origin: str = 'http://localhost:3000'
    llm_provider: Literal['local', 'anthropic'] = 'local'
    anthropic_api_key: str = ''
    anthropic_model: str = ''
    llm_timeout_seconds: float = 15.0

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{ROOT / 'backend' / 'triage.db'}"
