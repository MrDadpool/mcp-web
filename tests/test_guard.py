import ipaddress

import pytest

from mcp_web.config import Settings
from mcp_web.net.guard import BlockedURLError, validate_url

OPEN = Settings(allow_private=False, allowlist=frozenset())


def block(url, cfg=OPEN):
    with pytest.raises(BlockedURLError):
        validate_url(url, cfg)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080/admin",
        "http://localhost/",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://192.168.1.1/",
        "http://10.0.0.5/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::ffff:127.0.0.1]/",
        "http://2130706433/",       # decimal-encoded 127.0.0.1
        "http://0x7f000001/",       # hex-encoded 127.0.0.1
        "file:///etc/passwd",
        "ftp://example.com/",
        "http:///nohost",
    ],
)
def test_blocked(url):
    block(url)


def test_public_host_allowed(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [ipaddress.ip_address("93.184.216.34")],
    )
    assert validate_url("https://example.com/x", OPEN) == "https://example.com/x"


def test_dns_pointing_at_localhost_is_blocked(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [ipaddress.ip_address("127.0.0.1")],
    )
    block("https://evil.example.com/")


def test_any_resolved_address_private_blocks(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [
            ipaddress.ip_address("93.184.216.34"),
            ipaddress.ip_address("10.1.2.3"),
        ],
    )
    block("https://split.example.com/")


def test_allow_private_opt_in():
    cfg = Settings(allow_private=True, allowlist=frozenset())
    assert validate_url("http://127.0.0.1:1234/", cfg)


def test_allowlist(monkeypatch):
    monkeypatch.setattr(
        "mcp_web.net.guard.resolve_addresses",
        lambda host: [ipaddress.ip_address("93.184.216.34")],
    )
    cfg = Settings(allow_private=False, allowlist=frozenset({"example.com"}))
    assert validate_url("https://docs.example.com/a", cfg)
    with pytest.raises(BlockedURLError):
        validate_url("https://other.org/a", cfg)
