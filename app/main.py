from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging import configure_logging, logger
from app.security import verify_request_security
from app.slack_parser import parse_slack_payload
from app.telegram_sender import TelegramClient
from app.routing import resolve_chat_id


settings = get_settings()
configure_logging()

app = FastAPI(title="slack2tg")
telegram_client: TelegramClient | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global telegram_client
    telegram_client = TelegramClient()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global telegram_client
    if telegram_client is not None:
        await telegram_client.aclose()
        telegram_client = None


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "up"}


@app.get("/ready")
async def ready() -> JSONResponse:
    # Lightweight readiness: ensure required settings exist
    ok = bool(settings.telegram_bot_token and settings.default_chat_id)
    status = 200 if ok else 503
    return JSONResponse(status_code=status, content={"ready": ok})


@app.post("/hook/{route_key}")
async def hook(route_key: str, request: Request) -> JSONResponse:
    raw = await request.body()
    await verify_request_security(route_key, request, raw)
    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    logger.info("hook.received", extra={"route_key": route_key, "content_type": request.headers.get("content-type")})

    parsed = parse_slack_payload(payload)
    slack_channel = (payload.get("channel") or "").strip()
    chat_id = resolve_chat_id(route_key, slack_channel)

    tg = telegram_client or TelegramClient()
    # Media first
    if parsed.images:
        if len(parsed.images) > 1:
            await tg.send_media_group(chat_id, parsed.images, caption=parsed.images[0][1] or None)
        else:
            url, title = parsed.images[0]
            await tg.send_photo(chat_id, url, caption=title)
    for url, title in parsed.documents:
        await tg.send_document(chat_id, url, caption=title)

    # Then text in chunks
    await tg.send_text_chunked(chat_id, parsed.text)

    return JSONResponse(status_code=200, content={"ok": True})


