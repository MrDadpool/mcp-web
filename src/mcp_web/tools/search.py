"""DuckDuckGo search via the ddgs package."""

from __future__ import annotations

import anyio
from ddgs import DDGS


def _search(query: str, max_results: int, region: str) -> list[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, region=region, max_results=max_results))


async def web_search(query: str, max_results: int = 5, region: str = "wt-wt") -> list[dict]:
    """ddgs is synchronous, so it runs on a worker thread."""
    max_results = max(1, min(max_results, 25))
    raw = await anyio.to_thread.run_sync(_search, query, max_results, region)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href") or r.get("url", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw
    ]
