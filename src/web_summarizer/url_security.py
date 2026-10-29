"""URL validation that blocks common server-side request forgery targets."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Iterable
from urllib.parse import urlparse

from .exceptions import UnsafeURLError

Resolver = Callable[..., Iterable[tuple]]


def _is_blocked_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def validate_public_http_url(
    url: str,
    *,
    resolver: Resolver = socket.getaddrinfo,
) -> str:
    """Validate a public HTTP(S) URL and return its normalized form.

    Every redirect target must be passed through this function again.
    """

    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeURLError("Only http:// and https:// URLs are allowed.")
    if not parsed.hostname:
        raise UnsafeURLError("The URL must contain a hostname.")
    if parsed.username or parsed.password:
        raise UnsafeURLError("Credentials embedded in URLs are not allowed.")
    if parsed.hostname.lower() == "localhost":
        raise UnsafeURLError("Localhost URLs are not allowed.")

    try:
        direct_ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        direct_ip = None

    if direct_ip is not None and _is_blocked_ip(str(direct_ip)):
        raise UnsafeURLError("Private, local, or reserved IP addresses are blocked.")

    try:
        default_port = 443 if parsed.scheme == "https" else 80
        address_info = resolver(
            parsed.hostname,
            parsed.port or default_port,
            type=socket.SOCK_STREAM,
        )
    except OSError as exc:
        raise UnsafeURLError(f"Unable to resolve URL hostname: {exc}") from exc

    resolved_addresses = {entry[4][0] for entry in address_info}
    if not resolved_addresses:
        raise UnsafeURLError("The URL hostname did not resolve to an IP address.")

    for address in resolved_addresses:
        if _is_blocked_ip(address):
            raise UnsafeURLError(
                "The URL resolves to a private, local, or reserved IP address."
            )

    return parsed.geturl()

