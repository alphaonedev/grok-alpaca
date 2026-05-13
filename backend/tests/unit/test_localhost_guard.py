import pytest

from app.core.localhost_guard import NonLoopbackBindError, ensure_localhost


def test_loopback_accepts_ipv4():
    ensure_localhost("127.0.0.1")


def test_loopback_accepts_localhost():
    ensure_localhost("localhost")


def test_loopback_rejects_zero():
    with pytest.raises(NonLoopbackBindError):
        ensure_localhost("0.0.0.0")


def test_loopback_rejects_v6_unspec():
    with pytest.raises(NonLoopbackBindError):
        ensure_localhost("::")


def test_loopback_rejects_public_ip():
    with pytest.raises(NonLoopbackBindError):
        ensure_localhost("8.8.8.8")
