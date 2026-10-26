from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BRANDPROOF_", env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/brandproof.db"
    ai_provider: Literal["none", "groq", "openrouter"] = "none"
    ai_model: str = ""
    ai_api_key: SecretStr = SecretStr("")
    external_ai_enabled: bool = False
    ai_workspace_hourly_limit: int = Field(default=6, ge=0, le=10000)
    ai_global_hourly_limit: int = Field(default=24, ge=0, le=10000)
    ai_workspace_concurrency_limit: int = Field(default=1, ge=1, le=16)
    ai_global_concurrency_limit: int = Field(default=2, ge=1, le=16)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
