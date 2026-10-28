from typing import Literal

from pydantic import Field, SecretStr, field_validator
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
    demo_cookie_secure: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins")
    @classmethod
    def exact_cors_origins(cls, origins: list[str]) -> list[str]:
        if any("*" in origin or origin == "null" for origin in origins):
            raise ValueError("Credentialed CORS requires exact origins, not wildcards or null")
        return origins
