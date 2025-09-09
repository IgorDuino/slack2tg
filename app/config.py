from __future__ import annotations

from functools import lru_cache
from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_prefix="", case_sensitive=False)

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    default_chat_id: str = Field(default="", alias="DEFAULT_CHAT_ID")
    routing_map: str = Field(default="{}", alias="ROUTING_MAP")  # JSON string
    disable_web_preview: bool = Field(default=False, alias="DISABLE_WEB_PREVIEW")
    parse_mode: str = Field(default="MarkdownV2", alias="PARSE_MODE")
    max_media: int = Field(default=10, alias="MAX_MEDIA")
    shared_secret: str = Field(default="", alias="SHARED_SECRET")
    allow_ips: str = Field(default="", alias="ALLOW_IPS")  # CSV
    retry_max: int = Field(default=3, alias="RETRY_MAX")
    retry_backoff: float = Field(default=0.5, alias="RETRY_BACKOFF")

    uvicorn_workers: int = Field(default=1, alias="UVICORN_WORKERS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    json_logs: bool = Field(default=True, alias="JSON_LOGS")

    def routing_map_dict(self) -> Dict[str, str]:
        try:
            import json

            return json.loads(self.routing_map or "{}")
        except Exception:  # noqa: BLE001
            return {}

    def allow_ip_set(self) -> set[str]:
        return {ip.strip() for ip in (self.allow_ips or "").split(",") if ip.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


