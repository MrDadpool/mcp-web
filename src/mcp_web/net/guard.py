"""URL validation. Every outbound request in this server passes through here.

The threat model is a local LLM that has been talked into fetching a URL it
should not: the router admin page, a cloud metadata endpoint, another service
bound to localhost. Blocking by hostname string is not enough, so we resolve
the name and check every address it maps to.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

from ..config import Settings, settings

ALLOWED_SCHEMES = frozenset({"http", "https"})

# Cloud instance-metadata services. These live inside link-local space, which
# is already blocked, but they are called out so the denial reads clearly in
# logs and so the check survives anyone loosening the link-local rule.
METADATA_ADDRESSES = frozenset({"169.254.169.254", "fd00:ec2::254"})


class BlockedURLError(ValueError):
    """Raised when a URL must not be requested."""


def _address_is_forbidden(ip: ipaddress._BaseAddress) -> str | None:
    """Return a reason string if this address is off limits, else None."""
    if str(ip) in METADATA_ADDRESSES:
        return "cloud metadata endpoint"
    if ip.is_loopback:
        return "loopback address"
    if ip.is_private:
        return "private network address"
    if ip.is_link_local:
        return "link-local address"
    if ip.is_reserved or ip.is_multicast or ip.is_unspecified:
        return "reserved address"
    # An IPv4 address wearing an IPv6 costume, e.g. ::ffff:127.0.0.1.
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        return _address_is_forbidden(mapped)
    return None


def _host_allowed(host: str, allowlist: frozenset[str]) -> bool:
    if not allowlist:
        return True
    host = host.lower().rstrip(".")
    return any(host == entry or host.endswith("." + entry) for entry in allowlist)


def resolve_addresses(host: str) -> list[ipaddress._BaseAddress]:
    """Resolve a hostname to every address it maps to.

    A literal IP in the URL never reaches the resolver, so notations that DNS
    would not produce -- 0x7f.1, 2130706433, [::ffff:127.0.0.1] -- are parsed
    directly by ipaddress and checked the same way.
    """
    try:
        return [ipaddress.ip_address(host.strip("[]"))]
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise BlockedURLError(f"cannot resolve host {host!r}: {exc}") from exc
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def validate_url(url: str, cfg: Settings | None = None) -> str:
    """Check a URL and return it normalised, or raise BlockedURLError.

    Call this on the URL the model supplied *and* on every redirect target --
    a permitted host is free to redirect somewhere that is not.
    """
    cfg = cfg or settings
    parts = urlsplit(url)

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise BlockedURLError(
            f"scheme {parts.scheme!r} is not allowed; use http or https"
        )
    host = parts.hostname
    if not host:
        raise BlockedURLError(f"no host in URL {url!r}")

    if not _host_allowed(host, cfg.allowlist):
        raise BlockedURLError(
            f"host {host!r} is not in MCPWEB_ALLOWLIST"
        )

    if not cfg.allow_private:
        for ip in resolve_addresses(host):
            reason = _address_is_forbidden(ip)
            if reason:
                raise BlockedURLError(
                    f"refusing to reach {host} ({ip}): {reason}. "
                    "Set MCPWEB_ALLOW_PRIVATE=1 to permit local network access."
                )
    return url
