Slack Incoming Webhook → Telegram Bot bridge

Quick start

1. Copy .env.example to .env and set TELEGRAM_BOT_TOKEN and DEFAULT_CHAT_ID.
2. Run locally:

```
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Docker

```
docker build -t slack2tg .
docker run --rm -p 8080:8080 --env-file .env slack2tg
```

Endpoints

- POST /hook/{route_key}
- GET /healthz
- GET /ready

Security

- Token query param (?token=SHARED_SECRET) or HMAC headers: X-Signature=sha256=HEX and X-Timestamp=epoch seconds.
- Optional IP allowlist via ALLOW_IPS.


