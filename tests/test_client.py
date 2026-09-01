import ipaddress

import httpx
import pytest
import respx

from mcp_web.config import Settings
from mcp_web.net import client
from mcp_web.net.guard import BlockedURLError

CFG = Settings(allow_private=False, allowlist=frozenset(), max_bytes=100, max_redirects=2)


@pytest.fixture(autouse=True)
async def _public_dns(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [ipaddress.ip_address("93.184.216.34")],
    )
    yield
    await client.aclose()


@respx.mock
async def test_body_is_capped():
    respx.get("https://example.com/big").mock(
        return_value=httpx.Response(200, content=b"x" * 5000)
    )
    resp = await client.request("https://example.com/big", cfg=CFG)
    assert len(resp.body) == 100
    assert resp.truncated


@respx.mock
async def test_redirect_to_localhost_is_blocked(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [
            ipaddress.ip_address("127.0.0.1" if "evil" in host else "93.184.216.34")
        ],
    )
    respx.get("https://example.com/r").mock(
        return_value=httpx.Response(302, headers={"location": "http://evil.test/"})
    )
    with pytest.raises(BlockedURLError):
        await client.request("https://example.com/r", cfg=CFG)


@respx.mock
async def test_redirect_limit():
    respx.get("https://example.com/loop").mock(
        return_value=httpx.Response(302, headers={"location": "https://example.com/loop"})
    )
    with pytest.raises(BlockedURLError):
        await client.request("https://example.com/loop", cfg=CFG)


@respx.mock
async def test_post_downgrades_to_get_on_303():
    respx.post("https://example.com/p").mock(
        return_value=httpx.Response(303, headers={"location": "https://example.com/done"})
    )
    route = respx.get("https://example.com/done").mock(
        return_value=httpx.Response(200, content=b"ok")
    )
    resp = await client.request("https://example.com/p", method="POST", body="a=1", cfg=CFG)
    assert route.called
    assert resp.body == b"ok"
