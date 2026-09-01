import ipaddress

import httpx
import pytest
import respx

from mcp_web.net import client
from mcp_web.tools.fetch import fetch_url
from mcp_web.tools.http import http_request

HTML = """
<html><head><title>Real Title</title></head>
<body><nav>skip me</nav>
<article><h1>Heading</h1><p>This is the actual article body text, long enough
that trafilatura keeps it instead of discarding the page as boilerplate.</p>
</article></body></html>
"""


@pytest.fixture(autouse=True)
async def _public_dns(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [ipaddress.ip_address("93.184.216.34")],
    )
    yield
    await client.aclose()


@respx.mock
async def test_fetch_url_extracts_content():
    respx.get("https://example.com/a").mock(
        return_value=httpx.Response(
            200, content=HTML.encode(), headers={"content-type": "text/html"}
        )
    )
    out = await fetch_url("https://example.com/a")
    assert "actual article body" in out["content_markdown"]
    assert "skip me" not in out["content_markdown"]
    assert out["status"] == 200


@respx.mock
async def test_fetch_url_clips():
    respx.get("https://example.com/a").mock(
        return_value=httpx.Response(
            200, content=HTML.encode(), headers={"content-type": "text/html"}
        )
    )
    out = await fetch_url("https://example.com/a", max_chars=20)
    assert out["truncated"]


@respx.mock
async def test_http_request_strips_host_header():
    route = respx.get("https://example.com/api").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    out = await http_request(
        "https://example.com/api", headers={"Host": "evil.test", "X-Key": "v"}
    )
    sent = route.calls[0].request
    assert sent.headers["host"] == "example.com"
    assert sent.headers["x-key"] == "v"
    assert out["status"] == 200
