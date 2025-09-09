from __future__ import annotations

import asyncio
import json
from typing import List, Optional, Sequence, Tuple

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramServerError
from aiogram.types import FSInputFile, InputMediaPhoto

from app.config import get_settings
from app.formatting import chunk_text, escape_markdown_v2
from app.logging import logger


MESSAGE_LIMIT = 4096
CAPTION_LIMIT = 1024


class TelegramClient:
    def __init__(self, token: Optional[str] = None):
        settings = get_settings()
        self.bot = Bot(
            token=token or settings.telegram_bot_token,
            default=DefaultBotProperties(parse_mode=settings.parse_mode),
        )
        self.disable_web_preview = settings.disable_web_preview
        self.retry_max = settings.retry_max
        self.retry_backoff = settings.retry_backoff

    async def _retry_call(self, coro_factory, *args, **kwargs):
        attempt = 0
        while True:
            try:
                return await coro_factory(*args, **kwargs)
            except TelegramRetryAfter as e:  # type: ignore[no-untyped-def]
                delay = int(e.retry_after) + 1
                logger.warning("telegram.retry_after", delay=delay)
                await asyncio.sleep(delay)
            except (TelegramServerError,) as e:
                if attempt >= self.retry_max:
                    raise
                delay = (2 ** attempt) * self.retry_backoff
                logger.warning("telegram.server_error", attempt=attempt, delay=delay)
                await asyncio.sleep(delay)
                attempt += 1

    async def send_text_chunked(self, chat_id: str, text: str) -> None:
        if not text:
            return
        settings = get_settings()
        if settings.parse_mode == "MarkdownV2":
            text = escape_markdown_v2(text)
        chunks = chunk_text(text, MESSAGE_LIMIT)
        for chunk in chunks:
            await self._retry_call(
                self.bot.send_message,
                chat_id=chat_id,
                text=chunk,
                disable_web_page_preview=self.disable_web_preview,
            )

    async def send_media_group(self, chat_id: str, photos: Sequence[Tuple[str, Optional[str]]], caption: Optional[str]) -> None:
        if not photos:
            return
        medias: List[InputMediaPhoto] = []
        first = True
        for url, _title in photos[:10]:
            cap = None
            if first and caption:
                cap = escape_markdown_v2(caption)[:CAPTION_LIMIT]
                first = False
            medias.append(InputMediaPhoto(media=url, caption=cap))
        await self._retry_call(self.bot.send_media_group, chat_id=chat_id, media=medias)

    async def send_photo(self, chat_id: str, url: str, caption: Optional[str]) -> None:
        cap = escape_markdown_v2(caption or "")[:CAPTION_LIMIT] if caption else None
        await self._retry_call(self.bot.send_photo, chat_id=chat_id, photo=url, caption=cap)

    async def send_document(self, chat_id: str, url: str, caption: Optional[str]) -> None:
        cap = escape_markdown_v2(caption or "")[:CAPTION_LIMIT] if caption else None
        await self._retry_call(self.bot.send_document, chat_id=chat_id, document=url, caption=cap)


