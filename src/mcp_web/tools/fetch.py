"""Fetch a URL and return readable text."""

from __future__ import annotations

from ..extract import clip, extract
from ..net import client


async def fetch_url(url: str, max_chars: int = 20_000) -> dict:
    resp = await client.request(url)
    ctype = resp.headers.get("content-type", "")
    if "html" in ctype or not ctype:
        title, content = extract(resp.text, url=resp.final_url)
    else:
        title, content = None, resp.text
    content, clipped = clip(content, max_chars)
    return {
        "url": resp.final_url,
        "status": resp.status,
        "title": title,
        "content_markdown": content,
        "truncated": clipped or resp.truncated,
    }
