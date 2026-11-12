"""No JSON-RPC batching (`docs/protocol/v2/draft/transports.mdx:65-67`): ACP-BATCH-209, plus the
array evidence for ACP-TRANSPORT-001 and ACP-JSONRPC-005.

ACP v2 does not use JSON-RPC batches: "Senders MUST NOT send a JSON array of messages, and
receivers reject one with a single `-32600` (Invalid Request) response with `id: null`." The
sender MUST NOT binds the agent as a sender too: an agent that answers with an array fails
`ACP-TRANSPORT-001` (MANDATORY); `test_transport.py` judges the arrays it sees in an ordinary
exchange, and `test_array_reply_is_never_an_array` here judges the replies to the probe arrays.
That row is kept apart from `ACP-BATCH-209` (ADVISORY, the receiver clause has no RFC 2119
keyword) so an agent that ignores or crashes on an array fails only the ADVISORY rows.

The probes deliberately break the client's "valid ACP messages only" rule
(`transports.mdx:24`) and its "no arrays" rule (`transports.mdx:67`): the spec defines the
agent's answer for exactly that input, so the probe is legitimate.

**Every test here calls `skip_if_version_mismatch` on its own manual `initialize`**, unlike
`test_jsonrpc.py`. A v1-only agent forced under `--protocol-version 2` (per
`tck.v1.conformance._base`'s `run()`: a top-level JSON array is silently dropped, `isinstance(
message, dict)` gate, no reply at all) would otherwise time out and FAIL this file's rows,
breaking `tests/v2/test_cli.py`'s
`test_v1_conforming_agent_under_protocol_version_2_is_blocked_by_version_mismatch` invariant
(zero FAILs, full `VERSION-MISMATCH:` coverage for every non-negotiation id).
`_helpers.v2_only_agent` implements this "manual initialize + skip on mismatch" pattern.

Each probe array uses its own fresh connection (one `v2_only_agent` per case) where a reply is
judged: an array is exactly the kind of traffic that could crash a less battle-tested agent, and
isolating each probe means one crash cannot cascade into a sibling assertion.

Probe requests use `session/list` only when the agent advertises `capabilities.session`, and the
`_`-prefixed `_tck/does_not_exist` otherwise (only `initialize` is unconditional in v2).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.v2.protocol import INVALID_REQUEST

from ._helpers import (
    advertises_session,
    first_response_within,
    next_reply_line,
    quiet_period,
    v2_only_agent,
)

_REQUEST_IDS = ("tck-batch-a", "tck-batch-b")


def _probe_method(init_result) -> str:
    """A side-effect-free request every agent must answer: `session/list` when sessions are
    advertised, else an unknown `_`-prefixed method (which still gets a response)."""
    return "session/list" if advertises_session(init_result) else "_tck/does_not_exist"


def _probe_arrays(init_result) -> dict[str, list[Any]]:
    """The array shapes `ACP-BATCH-209` names, keyed by a test id."""
    method = _probe_method(init_result)
    return {
        "empty": [],
        "notification-only": [{"jsonrpc": "2.0", "method": "_tck/notify_only"}],
        "requests": [{"jsonrpc": "2.0", "id": req_id, "method": method} for req_id in _REQUEST_IDS],
        "non-objects": [17, True, None],
        "mixed-call-and-response": [
            {"jsonrpc": "2.0", "id": "tck-mixed-call", "method": "_tck/does_not_exist"},
            {"jsonrpc": "2.0", "id": "tck-mixed-response", "result": {}},
        ],
    }


_CASES = ("empty", "notification-only", "requests", "non-objects", "mixed-call-and-response")


@pytest.mark.requirement("ACP-BATCH-209")
@pytest.mark.parametrize("case", _CASES)
async def test_array_yields_a_single_invalid_request_object(agent_launch, case):
    """ACP-BATCH-209 (ADVISORY). Any JSON array on stdin -- empty, request-only,
    notification-only, non-object elements, or a mix of call- and response-shaped elements --
    gets exactly one `-32600` response *object* with `id: null`, and no element is processed:
    nothing else answers within the quiet period, in particular no response carries an
    element's id.

    The agent's own notifications or requests arriving first are skipped
    (`_helpers.next_reply_line`); the first other line is judged. Silence, a crash, per-element
    replies and an array reply all fail."""
    async with v2_only_agent(agent_launch, yield_result=True) as (agent, init_result):
        await agent.send_raw(json.dumps(_probe_arrays(init_result)[case]))
        try:
            entry = await next_reply_line(agent, agent_launch.default_timeout)
        except AgentTimeout:
            pytest.fail(f"no reply to a JSON array ({case}); expected one -32600 object")
        msg = entry.parsed
        assert isinstance(msg, dict), f"expected a single response object, got {entry.raw!r}"
        assert msg.get("id") is None, (
            f"expected id: null (no element may be processed), got {msg.get('id')!r}"
        )
        error = msg.get("error")
        assert isinstance(error, dict), f"expected an error object, got {msg!r}"
        assert error.get("code") == INVALID_REQUEST, f"expected -32600, got {error.get('code')!r}"

        extra = await first_response_within(agent, quiet_period(agent_launch.default_timeout))
        assert extra is None, f"more than one reply to a single JSON array: {extra.raw!r}"


@pytest.mark.requirement("ACP-TRANSPORT-001")
async def test_array_reply_is_never_an_array(agent_launch):
    """ACP-TRANSPORT-001 (MANDATORY). Whatever the agent does with the probe arrays, no line it
    writes to stdout is itself an array: senders MUST NOT send one (`transports.mdx:67`), the
    agent included. `test_transport.py` covers arrays in an ordinary exchange; this covers an
    array answered with an array.

    Only the *shape* of what the agent writes is judged here. Silence, a crash, or a rejection
    all pass -- `ACP-BATCH-209` owns whether the array was handled correctly."""
    async with v2_only_agent(agent_launch, yield_result=True) as (agent, init_result):
        try:
            for array in _probe_arrays(init_result).values():
                await agent.send_raw(json.dumps(array))
            quiet = quiet_period(agent_launch.default_timeout)
            while True:
                await agent.read_line(timeout=quiet)
        except (AgentTimeout, AgentExited):
            pass  # the quiet period elapsed, or the agent is gone: nothing more to read
        arrays = [
            entry.raw
            for entry in agent.transcript
            if entry.direction is Direction.RECEIVED and isinstance(entry.parsed, list)
        ]
        assert not arrays, f"agent wrote a JSON array to stdout (ACP has no batches): {arrays!r}"


@pytest.mark.requirement("ACP-JSONRPC-005")
async def test_connection_survives_a_rejected_array(agent_launch):
    """ACP-JSONRPC-005 (ADVISORY). After a rejected JSON array the connection is still usable:
    an ordinary follow-up request (`_probe_method`) gets an ordinary reply, matched by id so
    whatever the agent did with the array (an error object, or nothing) does not matter."""
    async with v2_only_agent(agent_launch, yield_result=True) as (agent, init_result):
        await agent.send_raw(json.dumps(_probe_arrays(init_result)["non-objects"]))
        follow_up_id = await agent.send_request(_probe_method(init_result))
        follow_up = await agent.wait_for_response(
            follow_up_id, timeout=agent_launch.default_timeout
        )
        assert isinstance(follow_up.parsed, dict) and (
            "result" in follow_up.parsed or "error" in follow_up.parsed
        ), f"connection did not survive the rejected array: {follow_up.raw!r}"
