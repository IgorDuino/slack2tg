from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.formatting import escape_markdown_v2


class ParsedSlackMessage:
    def __init__(self, text: str, images: List[Tuple[str, Optional[str]]], documents: List[Tuple[str, Optional[str]]]):
        self.text = text
        self.images = images
        self.documents = documents


def _render_blocks(blocks: List[Dict[str, Any]] | None) -> str:
    if not blocks:
        return ""
    lines: List[str] = []
    for block in blocks:
        btype = block.get("type")
        if btype == "section":
            text = _extract_text(block.get("text"))
            if text:
                lines.append(text)
        elif btype == "header":
            text = _extract_text(block.get("text"))
            if text:
                lines.append(f"*{text}*")
        elif btype == "divider":
            lines.append("\n———\n")
        elif btype == "context":
            elements = block.get("elements") or []
            parts = [_extract_text(el) for el in elements]
            parts = [p for p in parts if p]
            if parts:
                lines.append(" ".join(parts))
        else:
            continue
    return "\n".join([ln for ln in lines if ln])


def _extract_text(obj: Any) -> str:
    if not obj:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        txt = obj.get("text") or obj.get("alt_text") or ""
        return txt
    return ""


def _collect_media_attachments(attachments: List[Dict[str, Any]] | None) -> Tuple[List[Tuple[str, Optional[str]]], List[Tuple[str, Optional[str]]]]:
    images: List[Tuple[str, Optional[str]]] = []
    documents: List[Tuple[str, Optional[str]]] = []
    if not attachments:
        return images, documents
    for att in attachments:
        image_url = att.get("image_url") or att.get("thumb_url")
        title = att.get("title") or att.get("fallback")
        if image_url:
            images.append((image_url, title))
            continue
        file_url = att.get("file_url") or att.get("title_link")
        if file_url:
            documents.append((file_url, title))
    return images, documents


def parse_slack_payload(payload: Dict[str, Any]) -> ParsedSlackMessage:
    text = (payload.get("text") or "").strip()
    blocks = payload.get("blocks")
    attachments = payload.get("attachments")

    blocks_text = _render_blocks(blocks if isinstance(blocks, list) else None)
    combined_text = "\n\n".join([t for t in [text, blocks_text] if t])

    images, documents = _collect_media_attachments(attachments if isinstance(attachments, list) else None)

    # Optionally include username/icon info as preamble
    username = (payload.get("username") or "").strip()
    icon_emoji = (payload.get("icon_emoji") or "").strip()
    icon_url = (payload.get("icon_url") or "").strip()
    preamble = ""
    if username:
        preamble = f"From: {username}"
        if icon_emoji:
            preamble = f"{icon_emoji} {preamble}"
        elif icon_url:
            preamble = f"{preamble} ({icon_url})"

    if preamble:
        combined_text = f"{preamble}\n\n{combined_text}" if combined_text else preamble

    return ParsedSlackMessage(text=combined_text, images=images, documents=documents)


