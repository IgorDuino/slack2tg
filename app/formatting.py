from __future__ import annotations

from typing import Iterable, List


MARKDOWN_V2_RESERVED = set("_[]()~`>#+-=|{}.!\\*")


def escape_markdown_v2(text: str) -> str:
    # Escape all reserved characters for MarkdownV2
    return "".join(
        f"\\{ch}" if ch in MARKDOWN_V2_RESERVED else ch for ch in (text or "")
    )


def chunk_text(text: str, limit: int) -> List[str]:
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    chunks: List[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        # Try to split at a newline or space before the limit
        split_at = remaining.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit

        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip()

    return chunks


