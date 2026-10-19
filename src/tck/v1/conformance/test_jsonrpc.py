"""JSON-RPC envelope conformance: ACP-JSONRPC-001..007.

Separate from `test_transport.py`/`test_initialize.py` to keep the "jsonrpc:" group of
assertions in one focused file.

The TCK's own probe method, `_tck/does_not_exist`, is `_`-prefixed because the spec requires
custom methods to be (`docs/protocol/v1/draft/extensibility.mdx`) -- the TCK holds its own probe
traffic to the same rule it enforces on agents.
"""

from __future__ import annotations

import contextlib
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentProcess, AgentTimeout, Direction
from tck.v1.protocol import (
    METHOD_NOT_FOUND,
    PROTOCOL_VERSION,
    REQUEST_CANCELLED,
    STOP_REASON_CANCELLED,
)
from tck.v1.validation import validate_agent_response, validate_response_envelope

from ._helpers import (
    connected_agent,
    first_response_within,
    new_session,
    quiet_period,
    run_prompt,
    skip_if_version_mismatch,
)


@pytest.mark.requirement("ACP-JSONRPC-001")
async def test_id_is_echoed_for_integer_and_string_ids(agent_launch, tmp_path):
    """ACP-JSONRPC-001.

    Only ever sends one `initialize` per connection: a second one is unspecified in v1 and a
    strict agent may reject it with `-32600`, falsely FAILing an agent that echoes ids fine.
    The string-id half hand-rolls `session/new` instead of using `new_session`/
    `skip_if_auth_gated` -- id echo holds even for a `-32000` (auth-required) reply, so an
    auth-gated agent has nothing to break here."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        int_id = await agent.send_request(
            "initialize",
            {"protocolVersion": PROTOCOL_VERSION, "clientCapabilities": {}},
            id=424242,
        )
        int_entry = await agent.wait_for_response(int_id, timeout=agent_launch.default_timeout)
        assert int_entry.parsed["id"] == 424242, f"integer id not echoed: {int_entry.parsed!r}"

        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}, id="tck-string-id"
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        assert entry.parsed["id"] == "tck-string-id", f"string id not echoed: {entry.parsed!r}"


def _assert_valid_response_envelope(entry, *, what: str) -> None:
    msg = entry.parsed
    assert isinstance(msg, dict), f"{what} did not parse to a JSON object: {entry.raw!r}"
    issues = validate_response_envelope(msg)
    assert not issues, f"{what} response envelope is invalid: {issues!r} ({msg!r})"


@pytest.mark.requirement("ACP-JSONRPC-002")
async def test_response_envelope_is_result_xor_error_with_valid_shape(agent_launch):
    """ACP-JSONRPC-002. Uses only `initialize` and an invalid-params `session/new` (missing
    `cwd`), never a reply to an unrecognised method -- whether that reply exists at all is
    ACP-EXT-001's concern. Checks envelope shape only (`id`, `result` xor `error`), not which
    error code is used.
    """
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request(
            "initialize", {"protocolVersion": PROTOCOL_VERSION, "clientCapabilities": {}}
        )
        init_entry = await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)
        _assert_valid_response_envelope(init_entry, what="initialize")

        bad_id = await agent.send_request("session/new", {"mcpServers": []})  # missing required cwd
        bad_entry = await agent.wait_for_response(bad_id, timeout=agent_launch.default_timeout)
        _assert_valid_response_envelope(bad_entry, what="session/new (missing cwd)")


@pytest.mark.requirement("ACP-JSONRPC-004")
async def test_unknown_method_yields_method_not_found(agent_launch):
    """ACP-JSONRPC-004 (ADVISORY). Only the `-32601` code is a "should"; an agent that never
    replies SKIPs here, since replying at all is ACP-EXT-001's (MANDATORY) concern."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("_tck/does_not_exist")
        try:
            entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        except AgentTimeout:
            pytest.skip("agent never replied to the unknown method (ACP-EXT-001 judges that)")
        error = entry.parsed.get("error") if isinstance(entry.parsed, dict) else None
        assert error is not None, f"expected an error response, got {entry.parsed!r}"
        assert error.get("code") == METHOD_NOT_FOUND, f"expected -32601, got {error.get('code')!r}"


@pytest.mark.requirement("ACP-JSONRPC-003")
async def test_notification_receives_no_response(agent_launch, tmp_path):
    """ACP-JSONRPC-003. `session/cancel` with no prompt in flight is a pure notification.

    Also covers a would-be `ACP-CANCEL-003` (cancel itself gets no response) -- no separate id
    was registered since this test already asserts it.

    Uses `new_session()` (not a hand-rolled `session/new`) so it SKIPs via `skip_if_auth_gated`
    instead of crashing with a `KeyError` on an agent that gates `session/new` behind auth.

    Only a reply fails this (`_helpers.is_response_line`), not the agent's own notifications or
    requests."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        await agent.send_notification("session/cancel", {"sessionId": session_id})

        entry = await first_response_within(agent, quiet_period(agent_launch.default_timeout))
        assert entry is None, f"agent replied to a notification: {entry.text!r}"


@pytest.mark.requirement("ACP-JSONRPC-005")
async def test_connection_survives_an_erroneous_request(agent_launch, tmp_path):
    """ACP-JSONRPC-005 (ADVISORY -- see `tck.v1.requirements` for why this isn't MANDATORY).

    Silence on `_tck/does_not_exist` is ACP-EXT-001's concern, not this test's: the wait for
    that reply is bounded by `quiet_period()` with the timeout suppressed, so silence neither
    FAILs this row nor costs a full `--timeout`.

    Uses `new_session()` (not a hand-rolled `session/new`) so it SKIPs via `skip_if_auth_gated`
    instead of failing on an agent that gates `session/new` behind auth."""
    async with connected_agent(agent_launch) as agent:
        bad_id = await agent.send_request("_tck/does_not_exist")
        with contextlib.suppress(AgentTimeout):
            await agent.wait_for_response(bad_id, timeout=quiet_period(agent_launch.default_timeout))

        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert isinstance(session_id, str)


async def _assert_no_reply_to_notification(agent: AgentProcess, timeout: float, what: str) -> None:
    """Shared by the notification probes below. An agent that exits instead of replying sent no
    reply; whether the connection survives is judged by ACP-EXT-002/ACP-JSONRPC-006."""
    try:
        entry = await first_response_within(agent, quiet_period(timeout))
    except AgentExited:
        return
    assert entry is None, f"agent replied to {what}: {entry.text!r}"


@pytest.mark.requirement("ACP-JSONRPC-003")
async def test_custom_notification_receives_no_response(agent_launch):
    """ACP-JSONRPC-003, probed with an unrecognized `_`-prefixed notification."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification("_tck/notify", {})
        await _assert_no_reply_to_notification(
            agent, agent_launch.default_timeout, "a `_`-prefixed custom notification"
        )


@pytest.mark.requirement("ACP-JSONRPC-003")
async def test_cancel_request_for_unknown_id_receives_no_response(agent_launch):
    """ACP-JSONRPC-003, probed with `$/cancel_request` naming a request id never sent."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification("$/cancel_request", {"requestId": "tck-unknown"})
        await _assert_no_reply_to_notification(
            agent, agent_launch.default_timeout, "a `$/cancel_request` notification"
        )


@pytest.mark.requirement("ACP-JSONRPC-006")
async def test_connection_survives_cancel_request_for_unknown_id(agent_launch, tmp_path):
    """ACP-JSONRPC-006. Any reply to the notification is ACP-JSONRPC-003's concern; this only
    checks that `session/new` still succeeds afterwards."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification("$/cancel_request", {"requestId": "tck-unknown"})
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert isinstance(session_id, str)


def _last_sent_request_id(agent: AgentProcess, method: str) -> Any:
    for entry in reversed(agent.transcript):
        msg = entry.parsed
        if (
            entry.direction is Direction.SENT
            and isinstance(msg, dict)
            and msg.get("method") == method
            and "id" in msg
        ):
            return msg["id"]
    raise AssertionError(f"no {method} request was sent")


@pytest.mark.requirement("ACP-JSONRPC-007")
async def test_cancel_request_for_in_flight_prompt_gets_one_valid_response(
    agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text
):
    """ACP-JSONRPC-007. Sends `$/cancel_request` for the in-flight `session/prompt` at the same
    trigger point `run_prompt` uses for `session/cancel` (see `test_cancel.py`), with the same
    `--tck-cancel-prompt` text. SKIPs if the prompt resolved before the notification was sent.

    Unlike ACP-CANCEL-001, any valid result PASSes: the rule only constrains the response's
    shape, and an agent may not support `$/cancel_request` at all. As in `test_cancel.py`, a
    valid non-`cancelled` result within the race window (`quiet_period()`) of the notification
    SKIPs instead: the agent may have finished before reading it. After the response, another
    `quiet_period()` wait checks that no second response for the same id follows.

    No response within `--tck-timeout` SKIPs rather than FAILs: supporting `$/cancel_request`
    is optional and an agent may ignore it, so silence can't be told apart from a turn that is
    simply still running (e.g. one that waits for `session/cancel`). `session/cancel` is then
    sent so the turn ends; what that yields is ACP-CANCEL-001's concern."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        async def _send_cancel_request() -> None:
            prompt_id = _last_sent_request_id(agent, "session/prompt")
            await agent.send_notification("$/cancel_request", {"requestId": prompt_id})

        try:
            turn = await run_prompt(
                agent,
                session_id,
                [{"type": "text", "text": cancel_prompt_text}],
                on_action=_send_cancel_request,
                timeout=agent_launch.default_timeout,
            )
        except AgentTimeout:
            await agent.send_notification("session/cancel", {"sessionId": session_id})
            with contextlib.suppress(AgentTimeout, AgentExited):
                await agent.wait_for_response(
                    _last_sent_request_id(agent, "session/prompt"),
                    timeout=agent_launch.default_timeout,
                )
            pytest.skip(
                "cancellation not exercised: no response within --timeout after $/cancel_request "
                "(the agent may not support it, which is allowed)"
            )
        if turn.action_sent_at_index is None:
            pytest.skip(
                "cancellation not exercised: prompt turn completed before $/cancel_request "
                "could be sent"
            )

        race_window = quiet_period(agent_launch.default_timeout)
        msg = turn.response_entry.parsed
        assert isinstance(msg, dict), f"non-object response: {turn.response_entry.raw!r}"
        prompt_id = msg.get("id")
        if "error" in msg and "result" not in msg:
            error = msg["error"]
            code = error.get("code") if isinstance(error, dict) else None
            assert code == REQUEST_CANCELLED, (
                f"an error response after $/cancel_request must use code -32800, got {code!r}: "
                f"{turn.response_entry.text!r}"
            )
        else:
            issues = validate_agent_response("session/prompt", msg)
            assert not issues, f"session/prompt response after $/cancel_request is invalid: {issues!r}"
            result = msg.get("result")
            stop_reason = result.get("stopReason") if isinstance(result, dict) else None
            sent_at = agent.transcript[turn.action_sent_at_index].timestamp
            elapsed = turn.response_entry.timestamp - sent_at
            if stop_reason != STOP_REASON_CANCELLED and elapsed < race_window:
                pytest.skip(
                    f"cancellation not exercised: response arrived {elapsed * 1000:.0f} ms after "
                    "$/cancel_request; agent may have finished before reading it"
                )

        with contextlib.suppress(AgentTimeout, AgentExited):
            await agent.wait_for_message(
                lambda entry: entry.matches_id(prompt_id),
                timeout=quiet_period(agent_launch.default_timeout),
            )
    responses = [
        entry
        for entry in agent.transcript
        if entry.direction is Direction.RECEIVED and entry.matches_id(prompt_id)
    ]
    assert len(responses) == 1, (
        f"expected exactly one response to the cancelled session/prompt, got {len(responses)}: "
        f"{[entry.text for entry in responses]!r}"
    )
