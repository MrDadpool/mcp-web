"""HTML to readable markdown."""

from __future__ import annotations

import re

import trafilatura

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\n{3,}")


def extract(html: str, url: str | None = None) -> tuple[str | None, str]:
    """Return (title, markdown). Falls back to crude tag stripping."""
    content = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_links=True,
        include_tables=True,
        favor_recall=True,
    )
    title = None
    meta = trafilatura.extract_metadata(html)
    if meta is not None:
        title = meta.title

    if not content:
        content = _WS.sub("\n\n", _TAG.sub(" ", html)).strip()
    return title, content


def clip(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars].rstrip() + "\n\n[truncated]", True
