"""JSON-RPC envelope conformance: ACP-JSONRPC-001..005 and ACP-JSONRPC-202.

v2 counterpart of `tck.v1.conformance.test_jsonrpc` (honest duplication, not shared machinery).
`ACP-JSONRPC-005`'s second test lives in `test_batch.py` (the connection must survive a rejected
JSON array); the other ids are judged here on single messages.

Rows 001..005 need no `skip_if_version_mismatch`: a v1-only agent never receives an array probe
in this file, and its single-message replies are judged by the same rule v1 already holds it to.
`ACP-JSONRPC-202` judges the v2 `RequestId` rule against agent-authored requests, so it SKIPs
with `VERSION-MISMATCH:` for an agent that negotiated down.

Only `initialize` is unconditional in v2, so a probe uses a `session/*` method only when the agent
advertises `capabilities.session` (`_helpers.advertises_session`), and otherwise the `_`-prefixed
`_tck/does_not_exist` (every request gets a response; `extensibility.mdx:187`,
`overview.mdx:223`). `ACP-JSONRPC-202` needs a prompt turn to elicit requests, so it SKIPs when
`capabilities.session` is not advertised.
"""

from __future__ import annotations

import asyncio
import contextlib

import pytest

from tck.common.harness import AgentExited, AgentProcess, AgentTimeout
from tck.v2 import SPEC
from tck.v2.protocol import METHOD_NOT_FOUND
from tck.v2.validation import is_valid_request_id, validate_response_envelope

from ._helpers import (
    advertises_session,
    agent_requests,
    connected_agent,
    first_response_within,
    iter_messages,
    new_session,
    quiet_period,
    run_prompt,
    session_state_update,
    skip_if_version_mismatch,
)

_UNKNOWN_METHOD = "_tck/does_not_exist"


@pytest.mark.requirement("ACP-JSONRPC-001")
async def test_id_is_echoed_for_integer_and_string_ids(agent_launch, tmp_path):
    """ACP-JSONRPC-001. Sends one `initialize` per connection (a repeat is only specified before
    any other request, `ACP-INIT-212`). The integer-id half uses `initialize`
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
    which error code either response uses, only that the envelope is well-formed (exactly one
    of `result`/`error`, an integer or string `id` -- `null` only on an error -- and a valid
    error object). Both replies must also match the request's `id`, so a `null`-id result is
    seen as no reply at all, which fails the test."""
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


async def _assert_no_reply_to_notification(agent: AgentProcess, timeout: float, what: str) -> None:
    """Shared by the notification probes below. An agent that exits instead of replying sent no
    reply, so only a reply fails ACP-JSONRPC-003 here. An exit after `mcp/message` is
    `ACP-EXT-002`'s concern; one after `session/cancel` is only recorded (`ACP-INFO-CANCEL-201`)
    and judged by no row."""
    try:
        entry = await first_response_within(agent, quiet_period(timeout))
    except AgentExited:
        return
    assert entry is None, f"agent replied to {what}: {entry.text!r}"


@pytest.mark.requirement("ACP-JSONRPC-003")
async def test_notification_receives_no_response(agent_launch, agent_initialize_result, tmp_path):
    """ACP-JSONRPC-003. `session/cancel` with no prompt in flight is a pure notification; an
    agent that does not advertise `capabilities.session` gets a `_tck/notify` notification
    instead. Checks every message inside an array line too, not just a bare object line: an
    agent that folds a spurious response into an array alongside something else would otherwise
    pass this MANDATORY check by accident (the array itself is `ACP-TRANSPORT-001`'s concern).
    Only a reply fails this (`_helpers.is_response_line`),
    not the agent's own notifications or requests."""
    async with connected_agent(agent_launch) as agent:
        if advertises_session(agent_initialize_result.result):
            session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            await agent.send_notification("session/cancel", {"sessionId": session_id})
        else:
            await agent.send_notification("_tck/notify", {})

        await _assert_no_reply_to_notification(
            agent, agent_launch.default_timeout, "a notification"
        )


@pytest.mark.requirement("ACP-JSONRPC-003")
async def test_mcp_message_notification_receives_no_response(agent_launch):
    """ACP-JSONRPC-003, probed with `mcp/message` notifications (the unstable MCP-over-ACP
    envelope, `schema/v2/schema.unstable.json#/$defs/MessageMcpNotification`): a well-formed one
    for a request nothing is waiting on, and one missing the required `requestId` and `method`.
    Both break client rules on purpose: the envelope is sent only for an active request on a
    declared `acp` MCP server and only to an agent that advertised `acp`, and `requestId` and
    `method` are required. The spec defines the agent's answer to exactly these inputs:
    `overview.mdx:227` says notifications never receive responses, and the (Active)
    MCP-over-ACP RFD repeats it for this envelope (`mcp-over-acp.mdx:225,257`: no response,
    "malformed notifications do not receive synthetic replies"). Sent whether or not the agent
    advertises `capabilities.session.mcp.acp`: an agent that does not know the method must stay
    silent too. Only a reply fails this (`_helpers.is_response_line`); an agent that exits
    sent no reply, and `ACP-EXT-002` judges a crash."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification(
            "mcp/message",
            {
                "serverId": "tck-acp-1",
                "requestId": "tck-mcp-request-1",
                "method": "notifications/progress",
                "params": {"progressToken": "tck-progress", "progress": 1, "total": 2},
            },
        )
        await agent.send_notification("mcp/message", {"serverId": "tck-acp-1"})
        await _assert_no_reply_to_notification(
            agent, agent_launch.default_timeout, "an `mcp/message` notification"
        )


@pytest.mark.requirement("ACP-JSONRPC-004")
async def test_unknown_method_yields_method_not_found(agent_launch):
    """ACP-JSONRPC-004 (MANDATORY, `extensibility.mdx:202`, `error.mdx:44`). An unknown
    `_`-prefixed method gets `-32601`; the code is asserted because the MUST names it. Replying
    at all is `ACP-EXT-001`'s concern, so an agent that never replies SKIPs here rather than
    failing two rows for one defect."""
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


_PROMPT_TEXT = "hi"


@pytest.mark.requirement("ACP-JSONRPC-202")
async def test_agent_request_ids_are_strings_or_integers(agent_launch, agent_initialize_result, tmp_path):
    """ACP-JSONRPC-202 (id type; `overview.mdx:15-17`). Every request the agent sends during a
    prompt turn has an `id` that is a string or an integer, never `null`. SKIPs when the agent
    sends no request during the turn -- sending one is the agent's choice, so a quiet agent is
    not evidence of conformance."""
    _skip_unless_v2_session_agent(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
        requests = agent_requests(agent.transcript)
    if not requests:
        pytest.skip("the agent sent no request during the prompt turn, so no request id was observed")
    bad = [msg for msg in requests if not is_valid_request_id(msg["id"])]
    assert not bad, f"agent request ids must be a string or an integer, never null: {bad!r}"


@pytest.mark.requirement("ACP-JSONRPC-202")
async def test_agent_does_not_reuse_a_pending_request_id(agent_launch, agent_initialize_result, tmp_path):
    """ACP-JSONRPC-202 (no reuse while pending; `overview.mdx:19`). The TCK leaves every agent
    request unanswered for a quiet period (so each stays pending), then checks that no two share
    an `id`; it finally cancels the turn and answers them `cancelled`/`-32601` before closing.
    An agent that waits for the first answer before asking again never has two requests pending,
    so reuse is not observable and the test SKIPs, saying so."""
    _skip_unless_v2_session_agent(agent_initialize_result)
    timeout = agent_launch.default_timeout
    quiet = quiet_period(timeout)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    held: list[dict] = []
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        prompt_id = await agent.send_request(
            "session/prompt", {"sessionId": session_id, "prompt": [{"type": "text", "text": _PROMPT_TEXT}]}
        )
        turn_ended = False
        while not turn_ended:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                entry = await agent.read_line(timeout=min(remaining, quiet) if held else remaining)
            except AgentTimeout:
                break
            for msg in iter_messages(entry):
                if "method" in msg and "id" in msg:
                    held.append(msg)
                    continue
                update = session_state_update(msg, session_id)
                idle = update is not None and update.get("state") == "idle"
                rejected = entry.matches_id(prompt_id) and "error" in msg
                turn_ended = turn_ended or ((idle or rejected) and not held)

        if held:
            await agent.send_notification("session/cancel", {"sessionId": session_id})
            for msg in held:
                if msg["method"] == "session/request_permission":
                    reply = {"result": {"outcome": {"outcome": "cancelled"}}}
                else:
                    reply = {"error": {"code": METHOD_NOT_FOUND, "message": "Method not found"}}
                await agent.send_message({"jsonrpc": "2.0", "id": msg["id"], **reply})

    ids = [msg["id"] for msg in held if isinstance(msg["id"], (str, int)) and not isinstance(msg["id"], bool)]
    reused = sorted({repr(i) for i in ids if ids.count(i) > 1})
    assert not reused, f"agent reused request ids while they were still awaiting a response: {reused}"
    if len(held) < 2:
        pytest.skip(
            "the agent never had two requests pending at once during the prompt turn, so reuse of "
            "a pending id was not observable"
        )


def _skip_unless_v2_session_agent(outcome) -> None:
    """The `ACP-JSONRPC-202` tests elicit agent requests with a prompt turn, so they SKIP unless
    the agent speaks v2 (the rule is v2's `RequestId`) and advertises `capabilities.session`."""
    assert outcome.result is not None, f"initialize did not succeed: {outcome.error_message}"
    skip_if_version_mismatch(outcome.result)
    if not advertises_session(outcome.result):
        pytest.skip("capabilities.session not advertised, so no prompt turn can elicit requests")
