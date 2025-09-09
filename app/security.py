from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

from fastapi import HTTPException, Request

from app.config import get_settings


def _constant_time_equals(a: str, b: str) -> bool:
    try:
        return hmac.compare_digest(a, b)
    except Exception:  # noqa: BLE001
        return False


def _parse_signature_header(sig_header: Optional[str]) -> Optional[str]:
    if not sig_header:
        return None
    # Support forms: "sha256=<hex>" or raw hex
    if sig_header.lower().startswith("sha256="):
        return sig_header.split("=", 1)[1]
    return sig_header


def _verify_hmac_signature(body: bytes, timestamp: str | None, provided_sig: str | None, secret: str) -> bool:
    if not provided_sig or not timestamp:
        return False
    try:
        ts = int(timestamp)
    except Exception:  # noqa: BLE001
        return False

    # Reject if timestamp too old/new (5 min window)
    now = int(time.time())
    if abs(now - ts) > 300:
        return False

    # String to sign: "{timestamp}:{body}"
    message = f"{ts}:{body.decode('utf-8', errors='ignore')}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return _constant_time_equals(digest, provided_sig)


async def verify_request_security(route_key: str, request: Request, raw_body: bytes) -> None:
    settings = get_settings()

    # IP allowlist
    allow = settings.allow_ip_set()
    client_ip = (request.client.host if request.client else None) or ""
    if allow and client_ip not in allow:
        raise HTTPException(status_code=403, detail="Forbidden (IP)")

    # If no secret configured, allow
    if not settings.shared_secret:
        return

    # Accept either query token or HMAC signature
    token = request.query_params.get("token")
    if token and _constant_time_equals(token, settings.shared_secret):
        return

    sig_header = _parse_signature_header(request.headers.get("x-signature"))
    ts_header = request.headers.get("x-timestamp")
    if _verify_hmac_signature(raw_body, ts_header, sig_header, settings.shared_secret):
        return

    raise HTTPException(status_code=401, detail="Unauthorized")


