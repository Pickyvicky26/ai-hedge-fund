import os
import secrets
from urllib.parse import urlparse

from fastapi import Header, HTTPException, Request


def _normalize_host(value: str | None) -> str:
    if not value:
        return ""

    candidate = value.strip()
    if not candidate:
        return ""

    if "://" in candidate:
        parsed = urlparse(candidate)
        candidate = parsed.hostname or ""
    elif "/" in candidate:
        candidate = candidate.split("/", 1)[0]

    if candidate.startswith("[") and "]" in candidate:
        candidate = candidate[1:candidate.index("]")]
    elif candidate.count(":") == 1:
        candidate = candidate.split(":", 1)[0]

    return candidate.strip().lower()


def _is_loopback_host(host: str | None) -> bool:
    normalized = _normalize_host(host)
    return bool(normalized) and (
        normalized == "localhost"
        or normalized == "::1"
        or normalized.startswith("127.")
        or normalized.startswith("::ffff:127.")
    )


def _origin_is_local(request: Request) -> bool:
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    return _is_loopback_host(origin) or _is_loopback_host(referer)


async def require_local_or_admin(
    request: Request,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    configured_token = os.getenv("AI_HEDGE_FUND_ADMIN_TOKEN", "").strip()
    if configured_token and x_admin_token and secrets.compare_digest(x_admin_token, configured_token):
        return

    client_host = request.client.host if request.client else None
    if _is_loopback_host(client_host):
        if request.headers.get("origin") or request.headers.get("referer"):
            if _origin_is_local(request):
                return
        else:
            return

    raise HTTPException(
        status_code=403,
        detail=(
            "This endpoint is restricted to trusted local requests. "
            "For remote access, set AI_HEDGE_FUND_ADMIN_TOKEN on the backend "
            "and send it as X-Admin-Token."
        ),
    )
