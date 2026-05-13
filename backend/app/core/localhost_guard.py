"""Refuse to bind anywhere other than the loopback interface."""

from __future__ import annotations

import ipaddress
import socket

ALLOWED_HOSTNAMES = {"localhost", "ip6-localhost", "ip6-loopback"}


class NonLoopbackBindError(RuntimeError):
    pass


def _is_loopback(host: str) -> bool:
    if host in ALLOWED_HOSTNAMES:
        return True
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_loopback
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = info[4][0]
        try:
            if not ipaddress.ip_address(ip).is_loopback:
                return False
        except ValueError:
            return False
    return bool(infos)


def ensure_localhost(host: str) -> None:
    """Raise NonLoopbackBindError unless host is a loopback address/name."""
    if host in {"0.0.0.0", "::", "*"}:
        raise NonLoopbackBindError(
            f"refusing to bind to {host!r}: grok-alpaca is localhost-only"
        )
    if not _is_loopback(host):
        raise NonLoopbackBindError(
            f"refusing to bind to {host!r}: not a loopback address"
        )
