"""Runtime settings, all overridable by environment variable."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ["MCPWEB_" + name])
    except (KeyError, ValueError):
        return default


def _csv(name: str) -> frozenset[str]:
    raw = os.environ.get("MCPWEB_" + name, "")
    return frozenset(h.strip().lower() for h in raw.split(",") if h.strip())


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 mcp-web/0.1"
)


@dataclass(frozen=True)
class Settings:
    #: Allow requests to loopback / RFC1918 / link-local addresses.
    allow_private: bool = field(default_factory=lambda: _flag("MCPWEB_ALLOW_PRIVATE"))
    #: When non-empty, only these hostnames (and their subdomains) are reachable.
    allowlist: frozenset[str] = field(default_factory=lambda: _csv("ALLOWLIST"))
    timeout_s: float = field(default_factory=lambda: float(_int("TIMEOUT", 20)))
    max_bytes: int = field(default_factory=lambda: _int("MAX_BYTES", 2_000_000))
    max_redirects: int = field(default_factory=lambda: _int("MAX_REDIRECTS", 5))
    user_agent: str = field(
        default_factory=lambda: os.environ.get("MCPWEB_USER_AGENT", DEFAULT_USER_AGENT)
    )


settings = Settings()
