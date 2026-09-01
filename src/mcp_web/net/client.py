"""Shared HTTP client with size caps and hand-rolled redirect following.

Redirects are followed manually so that every hop can be re-validated by the
guard; httpx's own follow_redirects would jump to the final URL unchecked.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..config import Settings, settings
from .guard import BlockedURLError, validate_url

_client: httpx.AsyncClient | None = None


def get_client(cfg: Settings | None = None) -> httpx.AsyncClient:
    global _client
    if _client is None:
        cfg = cfg or settings
        _client = httpx.AsyncClient(
            follow_redirects=False,
            timeout=cfg.timeout_s,
            headers={"User-Agent": cfg.user_agent},
        )
    return _client


async def aclose() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes
    final_url: str
    truncated: bool

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


async def request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    cfg: Settings | None = None,
) -> Response:
    cfg = cfg or settings
    client = get_client(cfg)
    current = validate_url(url, cfg)

    for _ in range(cfg.max_redirects + 1):
        req = client.build_request(
            method.upper(),
            current,
            headers=headers,
            content=body.encode() if body is not None else None,
        )
        resp = await client.send(req, stream=True)
        try:
            if resp.is_redirect and resp.has_redirect_location:
                location = str(resp.next_request.url)
                current = validate_url(location, cfg)
                # A redirect chain may cross methods; mirror browser behaviour
                # by downgrading anything but HEAD to GET on 301/302/303.
                if resp.status_code in (301, 302, 303) and method.upper() != "HEAD":
                    method, body = "GET", None
                continue

            chunks: list[bytes] = []
            size = 0
            truncated = False
            async for chunk in resp.aiter_bytes():
                chunks.append(chunk)
                size += len(chunk)
                if size >= cfg.max_bytes:
                    truncated = True
                    break
            return Response(
                status=resp.status_code,
                headers=dict(resp.headers),
                body=b"".join(chunks)[: cfg.max_bytes],
                final_url=str(resp.url),
                truncated=truncated,
            )
        finally:
            await resp.aclose()

    raise BlockedURLError(f"too many redirects (limit {cfg.max_redirects})")
