"""JSON-RPC envelope conformance: ACP-JSONRPC-001..005.

v2 counterpart of `tck.v1.conformance.test_jsonrpc` (honest duplication, not shared machinery).
Per `tck.v2.requirements`, all five ids reuse their v1 wire assertions unchanged, widened only to
also cover a batch-delivered response/notification/erroneous-request -- but this file's own
probes are single-message only. That batch half of the evidence lives entirely in
`test_batch.py` (`@pytest.mark.requirement(...)` markers in both files jointly satisfy each id);
see its `test_batch_responses_echo_request_ids`,
`test_notification_only_batch_gets_no_reply`, and
`test_invalid_batch_entries_get_per_entry_invalid_request`.

No row here needs `skip_if_version_mismatch`: a v1-only agent never receives a batch-shaped probe
in this file, and its single-message replies are judged by the same rule v1 already holds it to.

Only `initialize` is unconditional in v2, so a probe uses a `session/*` method only when the agent
advertises `capabilities.session` (`_helpers.advertises_session`), and otherwise the `_`-prefixed
`_tck/does_not_exist` (every request gets a response; extensibility.mdx:178, overview.mdx:193).
"""

from __future__ import annotations

import contextlib

import pytest

from tck.common.harness import AgentTimeout
from tck.v2 import SPEC
from tck.v2.protocol import METHOD_NOT_FOUND
from tck.v2.validation import validate_response_envelope

from ._helpers import advertises_session, connected_agent, first_response_within, new_session, quiet_period

_UNKNOWN_METHOD = "_tck/does_not_exist"


@pytest.mark.requirement("ACP-JSONRPC-001")
async def test_id_is_echoed_for_integer_and_string_ids(agent_launch, tmp_path):
    """ACP-JSONRPC-001. Only ever sends one `initialize` per connection (a second `initialize` on
    an already-initialized connection is unspecified). The integer-id half uses `initialize`
    itself (a request every agent MUST answer); the string-id half sends `session/new` when the
    agent advertises `capabilities.session`, else `_tck/does_not_exist` -- id echo holds even for
    an error reply, so there is nothing here for an auth-gated or otherwise erroring agent to
    break."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        int_id = await agent.send_request("initialize", SPEC.initialize_params(), id=424242)
        int_entry = await agent.wait_for_response(int_id, timeout=agent_launch.default_timeout)
        assert int_entry.parsed["id"] == 424242, f"integer id not echoed: {int_entry.parsed!r}"

        if advertises_session(int_entry.parsed.get("result")):
            req_id = await agent.send_request("session/new", {"cwd": str(tmp_path)}, id="tck-string-id")
        else:
            req_id = await agent.send_request(_UNKNOWN_METHOD, id="tck-string-id")
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        assert entry.parsed["id"] == "tck-string-id", f"string id not echoed: {entry.parsed!r}"


def _assert_valid_response_envelope(entry, *, what: str) -> None:
    msg = entry.parsed
    assert isinstance(msg, dict), f"{what} did not parse to a JSON object: {entry.raw!r}"
    issues = validate_response_envelope(msg)
    assert not issues, f"{what} response envelope is invalid: {issues!r} ({msg!r})"


@pytest.mark.requirement("ACP-JSONRPC-002")
async def test_response_envelope_is_result_xor_error_with_valid_shape(agent_launch):
    """ACP-JSONRPC-002. Evidence: `initialize`'s own response, plus the error response to a
    deliberately invalid-params `session/new` (missing the required `cwd`) when the agent
    advertises `capabilities.session`, or to `_tck/does_not_exist` otherwise. Does not assert
    which error code either response uses, only that the envelope is well-formed."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", SPEC.initialize_params())
        init_entry = await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)
        _assert_valid_response_envelope(init_entry, what="initialize")

        init_msg = init_entry.parsed
        if advertises_session(init_msg.get("result") if isinstance(init_msg, dict) else None):
            what = "session/new (missing cwd)"
            bad_id = await agent.send_request("session/new", {})
        else:
            what = _UNKNOWN_METHOD
            bad_id = await agent.send_request(_UNKNOWN_METHOD)
        bad_entry = await agent.wait_for_response(bad_id, timeout=agent_launch.default_timeout)
        _assert_valid_response_envelope(bad_entry, what=what)


@pytest.mark.requirement("ACP-JSONRPC-003")
async def test_notification_receives_no_response(agent_launch, agent_initialize_result, tmp_path):
    """ACP-JSONRPC-003. `session/cancel` with no prompt in flight is a pure notification; an
    agent that does not advertise `capabilities.session` gets a `_tck/notify` notification
    instead. Checks every message inside a batch-array line too, not just a bare object line: an
    agent that folds a spurious response into a batch alongside something else would otherwise
    pass this MANDATORY check by accident. Only a reply fails this (`_helpers.is_response_line`),
    not the agent's own notifications or requests."""
    async with connected_agent(agent_launch) as agent:
        if advertises_session(agent_initialize_result.result):
            session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            await agent.send_notification("session/cancel", {"sessionId": session_id})
        else:
            await agent.send_notification("_tck/notify", {})

        entry = await first_response_within(agent, quiet_period(agent_launch.default_timeout))
        assert entry is None, f"agent replied to a notification: {entry.text!r}"


@pytest.mark.requirement("ACP-JSONRPC-004")
async def test_unknown_method_yields_method_not_found(agent_launch):
    """ACP-JSONRPC-004 (ADVISORY -- only the `-32601` code is "should"; replying at all is
    `ACP-EXT-001`'s MUST). An agent that never replies therefore SKIPs here rather than failing
    an ADVISORY row for a MANDATORY defect."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(_UNKNOWN_METHOD)
        try:
            entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        except AgentTimeout:
            pytest.skip("agent never replied to the unknown method (ACP-EXT-001 owns that)")
        error = entry.parsed.get("error") if isinstance(entry.parsed, dict) else None
        assert error is not None, f"expected an error response, got {entry.parsed!r}"
        assert error.get("code") == METHOD_NOT_FOUND, f"expected -32601, got {error.get('code')!r}"


@pytest.mark.requirement("ACP-JSONRPC-005")
async def test_connection_survives_an_erroneous_request(agent_launch, agent_initialize_result, tmp_path):
    """ACP-JSONRPC-005 (ADVISORY). After an unknown-method request, an ordinary request still gets
    an ordinary reply: `session/new` (its result shape asserted by `new_session`) when the agent
    advertises `capabilities.session`, else a second `_tck/does_not_exist` (any reply). A missing
    reply to the first request is `ACP-EXT-001`'s concern, so its wait is bounded by
    `quiet_period()` and a timeout is suppressed."""
    async with connected_agent(agent_launch) as agent:
        bad_id = await agent.send_request(_UNKNOWN_METHOD)
        with contextlib.suppress(AgentTimeout):
            await agent.wait_for_response(bad_id, timeout=quiet_period(agent_launch.default_timeout))

        if advertises_session(agent_initialize_result.result):
            await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            return
        follow_up_id = await agent.send_request(_UNKNOWN_METHOD)
        follow_up = await agent.wait_for_response(follow_up_id, timeout=agent_launch.default_timeout)
        assert isinstance(follow_up.parsed, dict) and (
            "result" in follow_up.parsed or "error" in follow_up.parsed
        ), f"connection did not survive the erroneous request: {follow_up.raw!r}"
