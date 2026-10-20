"""`InitializeOutcome.version_rejected`: the cached main handshake's `-32022` detection that drives
the version-rejection gate in `tck.common.plugin`."""

from __future__ import annotations

from tck.common.plugin import UNSUPPORTED_PROTOCOL_VERSION, InitializeOutcome


def test_unsupported_protocol_version_error_is_a_rejection() -> None:
    error = {"code": -32022, "message": "Unsupported protocol version", "data": {"requested": 1, "supported": [2]}}
    assert UNSUPPORTED_PROTOCOL_VERSION == -32022
    assert InitializeOutcome(None, "rejected", error).version_rejected


def test_other_error_codes_are_not_a_rejection() -> None:
    for code in (-32602, -32600, -32603, -32000):
        assert not InitializeOutcome(None, "failed", {"code": code, "message": "x"}).version_rejected


def test_success_and_transport_failures_are_not_a_rejection() -> None:
    assert not InitializeOutcome({"protocolVersion": 1}, None).version_rejected
    assert not InitializeOutcome(None, "agent exited").version_rejected
