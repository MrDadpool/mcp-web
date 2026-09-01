"""Headless rendering for pages that need JavaScript.

Imported only when playwright is installed; server.py skips registering the
tool otherwise. The browser starts on first use and is reused after that.
"""

from __future__ import annotations

import anyio

from ..config import settings
from ..extract import clip, extract
from ..net.guard import validate_url

_lock = anyio.Lock()
_playwright = None
_browser = None


async def _get_browser():
    global _playwright, _browser
    async with _lock:
        if _browser is None:
            from playwright.async_api import async_playwright

            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(headless=True)
    return _browser


async def shutdown() -> None:
    global _playwright, _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None


async def render_page(url: str, max_chars: int = 20_000, wait_ms: int = 1500) -> dict:
    validate_url(url)
    browser = await _get_browser()
    context = await browser.new_context(user_agent=settings.user_agent)
    try:
        page = await context.new_page()
        # Redirects inside the browser bypass the guard, so re-check where we
        # actually landed before handing any of it back to the model.
        with anyio.fail_after(settings.timeout_s):
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(min(wait_ms, 10_000))
            html = await page.content()
            final_url = page.url
        validate_url(final_url)
        title, content = extract(html, url=final_url)
        content, clipped = clip(content, max_chars)
        return {
            "url": final_url,
            "title": title or await page.title(),
            "content_markdown": content,
            "truncated": clipped,
        }
    finally:
        await context.close()
