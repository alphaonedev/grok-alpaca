"""Application settings loaded from .env and environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    xai_api_key: SecretStr = SecretStr("")
    alpaca_api_key: SecretStr = SecretStr("")
    alpaca_secret_key: SecretStr = SecretStr("")
    alpaca_data_feed: Literal["iex", "sip"] = "iex"

    host: str = "127.0.0.1"
    port: int = 8000

    log_level: str = "INFO"
    log_format: Literal["console", "json"] = "console"

    grok_model: str = "grok-4-0709"
    grok_temperature: float = 0.3
    grok_max_tool_rounds: int = 8

    data_dir: Path = Field(default=Path("~/.grok-alpaca"))

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"]
    )

    def model_post_init(self, __context) -> None:
        self.data_dir = self.data_dir.expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
