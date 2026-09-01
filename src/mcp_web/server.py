"""MCP server entrypoint. Speaks stdio; LM Studio spawns it per session."""

from __future__ import annotations

import logging
import sys
from importlib.util import find_spec

from mcp.server.mcpserver import MCPServer

from .net import client
from .net.guard import BlockedURLError
from .tools.fetch import fetch_url as _fetch_url
from .tools.http import http_request as _http_request
from .tools.search import web_search as _web_search

# stdout belongs to the MCP protocol; anything we say goes to stderr.
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
log = logging.getLogger("mcp-web")

mcp = MCPServer("mcp-web")

HAS_BROWSER = find_spec("playwright") is not None


def _error(exc: Exception) -> dict:
    """Tools return errors as data. An exception across stdio ends the session."""
    kind = "blocked" if isinstance(exc, BlockedURLError) else type(exc).__name__
    return {"error": f"{kind}: {exc}"}


@mcp.tool()
async def web_search(query: str, max_results: int = 5, region: str = "wt-wt") -> dict:
    """Search the web with DuckDuckGo.

    Returns a list of results with title, url and snippet. Follow up with
    fetch_url on any result whose full text you need.
    """
    try:
        return {"results": await _web_search(query, max_results, region)}
    except Exception as exc:  # noqa: BLE001 - surfaced to the model as data
        log.warning("web_search failed: %s", exc)
        return _error(exc)


@mcp.tool()
async def fetch_url(url: str, max_chars: int = 20_000) -> dict:
    """Fetch a web page and return its main content as markdown.

    Use this for ordinary pages and articles. If the result looks empty or is
    obviously a JavaScript shell, retry with render_page.
    """
    try:
        return await _fetch_url(url, max_chars)
    except Exception as exc:  # noqa: BLE001
        log.warning("fetch_url failed: %s", exc)
        return _error(exc)


@mcp.tool()
async def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    max_chars: int = 20_000,
) -> dict:
    """Make an arbitrary HTTP request and return the raw response.

    Use this for JSON APIs. For reading web pages prefer fetch_url, which
    strips navigation and boilerplate.
    """
    try:
        return await _http_request(url, method, headers, body, max_chars)
    except Exception as exc:  # noqa: BLE001
        log.warning("http_request failed: %s", exc)
        return _error(exc)


if HAS_BROWSER:
    from .tools.browser import render_page as _render_page

    @mcp.tool()
    async def render_page(url: str, max_chars: int = 20_000, wait_ms: int = 1500) -> dict:
        """Load a page in a headless browser, run its JavaScript, return the text.

        Slower than fetch_url. Use it only when fetch_url returns an empty or
        placeholder page.
        """
        try:
            return await _render_page(url, max_chars, wait_ms)
        except Exception as exc:  # noqa: BLE001
            log.warning("render_page failed: %s", exc)
            return _error(exc)


def main() -> None:
    log.info("mcp-web starting (browser tools: %s)", "on" if HAS_BROWSER else "off")
    try:
        mcp.run()
    finally:
        import anyio

        async def _cleanup() -> None:
            await client.aclose()
            if HAS_BROWSER:
                from .tools import browser

                await browser.shutdown()

        anyio.run(_cleanup)


if __name__ == "__main__":
    main()
