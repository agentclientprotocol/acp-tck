"""`tck.v2.conformance._helpers.advertises_session`: the gate non-session tests use before calling
any `session/*` method."""

from __future__ import annotations

from tck.v2.conformance._helpers import advertises_session


def test_session_object_marker_counts_even_when_empty() -> None:
    assert advertises_session({"capabilities": {"session": {}}})
    assert advertises_session({"capabilities": {"session": {"prompt": {}}}})


def test_absent_or_null_session_does_not_count() -> None:
    assert not advertises_session({"capabilities": {}})
    assert not advertises_session({"capabilities": {"session": None}})
    assert not advertises_session({})
    assert not advertises_session(None)


def test_v1_shaped_result_does_not_count() -> None:
    assert not advertises_session({"protocolVersion": 1, "agentCapabilities": {"loadSession": True}})
