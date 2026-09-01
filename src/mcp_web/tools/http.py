"""Raw HTTP access, for APIs rather than pages."""

from __future__ import annotations

from ..extract import clip
from ..net import client

# Hop-by-hop and identity headers the caller has no business setting.
BLOCKED_REQUEST_HEADERS = frozenset({"host", "content-length", "connection"})


async def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    max_chars: int = 20_000,
) -> dict:
    safe = {
        k: v
        for k, v in (headers or {}).items()
        if k.lower() not in BLOCKED_REQUEST_HEADERS
    }
    resp = await client.request(url, method=method, headers=safe, body=body)
    text, clipped = clip(resp.text, max_chars)
    return {
        "status": resp.status,
        "url": resp.final_url,
        "headers": resp.headers,
        "body": text,
        "truncated": clipped or resp.truncated,
    }
