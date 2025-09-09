from __future__ import annotations

from typing import Dict

from app.config import get_settings


def resolve_chat_id(route_key: str, slack_channel: str | None) -> str:
    settings = get_settings()
    mapping = settings.routing_map_dict()
    if route_key and route_key in mapping:
        return mapping[route_key]
    if slack_channel and slack_channel in mapping:
        return mapping[slack_channel]
    return settings.default_chat_id


