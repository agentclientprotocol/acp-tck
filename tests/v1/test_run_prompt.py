"""Unit tests for `tck.v1.conformance._helpers.run_prompt`'s permission handling, driven
against a tiny scripted stdio agent: once it reads `session/prompt` it replays a JSON plan of
messages to write (`"$ID"` stands for the prompt's request id), `{"wait_id": i}` (read until the
response to `i`) or `{"wait_method": m}`.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from tck.common.harness import AgentLaunch, AgentProcess, Direction
from tck.common.plugin import _TEST_PROPERTIES
from tck.v1.conformance._helpers import (
    UNKNOWN_PERMISSION_OPTION_ID,
    permission_outcome,
    run_prompt,
)

_SCRIPT = r"""
import json, sys
plan = json.loads(sys.argv[1])
def out(m):
    sys.stdout.write(json.dumps(m) + "\n"); sys.stdout.flush()
def read_until(pred):
    for line in sys.stdin:
        m = json.loads(line)
        if pred(m):
            return m
    sys.exit(0)
prompt = read_until(lambda m: m.get("method") == "session/prompt")
for step in plan:
    if "wait_method" in step:
        read_until(lambda m, w=step["wait_method"]: m.get("method") == w)
    elif "wait_id" in step:
        read_until(lambda m, w=step["wait_id"]: "method" not in m and m.get("id") == w)
    else:
        out(json.loads(json.dumps(step).replace('"$ID"', json.dumps(prompt["id"]))))
for line in sys.stdin:
    pass
"""

_SESSION = "s1"
_RESPONSE = {"jsonrpc": "2.0", "id": "$ID", "result": {"stopReason": "end_turn"}}


def _permission_request(options: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": "perm-1",
        "method": "session/request_permission",
        "params": {"sessionId": _SESSION, "toolCall": {"toolCallId": "t1"}, "options": options},
    }


def _permission_steps(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_permission_request(options), {"wait_id": "perm-1"}, _RESPONSE]


def _drive(steps: list[dict[str, Any]], **kwargs: Any):
    async def go():
        launch = AgentLaunch(
            command=[sys.executable, "-c", _SCRIPT, json.dumps(steps)],
            startup_timeout=2.0,
            default_timeout=2.0,
        )
        async with AgentProcess(launch) as agent:
            turn = await run_prompt(
                agent, _SESSION, [{"type": "text", "text": "hi"}], timeout=3.0, **kwargs
            )
            return agent, turn

    return asyncio.run(go())


def _sent_answer(agent, request_id: str) -> tuple[int, dict[str, Any]]:
    for index, entry in enumerate(agent.transcript):
        msg = entry.parsed
        if entry.direction is Direction.SENT and isinstance(msg, dict) and msg.get("id") == request_id:
            return index, msg
    raise AssertionError(f"no answer sent for {request_id!r}")


def _opts(*kinds: str) -> list[dict[str, Any]]:
    return [{"optionId": f"id-{i}-{kind}", "name": kind, "kind": kind} for i, kind in enumerate(kinds)]


def _selected(option_id: Any) -> dict[str, Any]:
    return {"outcome": "selected", "optionId": option_id}


def test_allow_picks_allow_once_regardless_of_position():
    outcome, note = permission_outcome(
        _opts("allow_always", "reject_once", "allow_once"), "allow"
    )
    assert outcome == _selected("id-2-allow_once")
    assert note is None


def test_allow_falls_back_to_allow_always_and_says_so():
    outcome, note = permission_outcome(_opts("reject_once", "allow_always"), "allow")
    assert outcome == _selected("id-1-allow_always")
    assert note == "allow_always selected (allow_once not offered)"


def test_allow_without_any_allow_option_falls_back_to_the_first_option():
    outcome, note = permission_outcome(_opts("reject_once", "reject_always"), "allow")
    assert outcome == _selected("id-0-reject_once")
    assert note == "first option selected (no allow_once offered)"


def test_reject_once_picks_reject_once_regardless_of_position():
    outcome, note = permission_outcome(_opts("allow_once", "reject_always", "reject_once"), "reject_once")
    assert outcome == _selected("id-2-reject_once")
    assert note is None


def test_reject_once_never_falls_back_to_another_option_kind():
    for kinds in (("allow_once", "reject_always"), ("allow_once", "allow_always"), ()):
        outcome, note = permission_outcome(_opts(*kinds), "reject_once")
        assert outcome == {"outcome": "cancelled"}
        assert note == "agent offered no reject_once option"


def test_unknown_option_selects_an_unoffered_underscore_prefixed_id():
    options = _opts("allow_once", "reject_once")
    outcome, note = permission_outcome(options, "unknown_option")
    assert outcome == _selected(UNKNOWN_PERMISSION_OPTION_ID)
    assert UNKNOWN_PERMISSION_OPTION_ID.startswith("_")
    assert UNKNOWN_PERMISSION_OPTION_ID not in {o["optionId"] for o in options}
    assert note is None


def test_cancelled_policy_answers_cancelled():
    assert permission_outcome(_opts("allow_once"), "cancelled") == ({"outcome": "cancelled"}, None)


def test_malformed_or_missing_options_do_not_crash():
    assert permission_outcome(None, "allow")[0] == _selected(None)
    assert permission_outcome(["junk", {"kind": "allow_once", "optionId": "x"}], "allow") == (
        _selected("x"),
        None,
    )
    assert permission_outcome([], "reject_once")[0] == {"outcome": "cancelled"}


def _assert_answered(agent, request_id: str, outcome: dict[str, Any]) -> None:
    _, answer = _sent_answer(agent, request_id)
    assert answer["result"]["outcome"] == outcome


def _recording(steps: list[dict[str, Any]], **kwargs: Any):
    """Run `_drive` with a per-test property list in scope; returns (agent, turn, properties)."""
    props: list[tuple[str, object]] = []
    token = _TEST_PROPERTIES.set(props)
    try:
        agent, turn = _drive(steps, **kwargs)
    finally:
        _TEST_PROPERTIES.reset(token)
    return agent, turn, props


def test_default_policy_selects_allow_once_not_the_first_option():
    options = [
        {"optionId": "always", "name": "Always", "kind": "allow_always"},
        {"optionId": "once", "name": "Once", "kind": "allow_once"},
    ]
    agent, turn, props = _recording(_permission_steps(options))
    _assert_answered(agent, "perm-1", {"outcome": "selected", "optionId": "once"})
    assert turn.permission_fallbacks == []
    assert props == []


def test_allow_always_fallback_is_recorded_on_the_turn_and_the_report_property():
    options = [
        {"optionId": "no", "name": "No", "kind": "reject_once"},
        {"optionId": "always", "name": "Always", "kind": "allow_always"},
    ]
    agent, turn, props = _recording(_permission_steps(options))
    _assert_answered(agent, "perm-1", {"outcome": "selected", "optionId": "always"})
    note = "allow_always selected (allow_once not offered)"
    assert turn.permission_fallbacks == [note]
    assert props == [("acp_tck_permission_fallback", note)]


def test_reject_once_policy_selects_the_reject_option():
    options = [
        {"optionId": "yes", "name": "Yes", "kind": "allow_once"},
        {"optionId": "no", "name": "No", "kind": "reject_once"},
    ]
    agent, _, _ = _recording(_permission_steps(options), permission="reject_once")
    _assert_answered(agent, "perm-1", {"outcome": "selected", "optionId": "no"})


def test_reject_once_without_a_reject_option_cancels_the_turn_instead_of_selecting_any_option():
    options = [
        {"optionId": "always", "name": "Always", "kind": "allow_always"},
        {"optionId": "once", "name": "Once", "kind": "allow_once"},
    ]
    steps = [
        _permission_request(options),
        {"wait_method": "session/cancel"},
        {"wait_id": "perm-1"},
        {"jsonrpc": "2.0", "id": "$ID", "result": {"stopReason": "cancelled"}},
    ]
    agent, turn, props = _recording(steps, permission="reject_once")
    answer_index, answer = _sent_answer(agent, "perm-1")
    assert answer["result"]["outcome"] == {"outcome": "cancelled"}
    cancels = [
        i for i, e in enumerate(agent.transcript)
        if e.direction is Direction.SENT and (e.parsed or {}).get("method") == "session/cancel"
    ]
    assert len(cancels) == 1 and cancels[0] < answer_index
    assert agent.transcript[cancels[0]].parsed["params"] == {"sessionId": _SESSION}
    assert turn.cancelled_at_index == cancels[0]
    note = "agent offered no reject_once option"
    assert turn.permission_cancels == [note]
    assert turn.permission_fallbacks == []
    assert props == [("acp_tck_permission_fallback", note)]
    assert turn.response_entry.parsed["result"]["stopReason"] == "cancelled"


def test_unknown_option_policy_selects_an_unoffered_id():
    options = [{"optionId": "yes", "name": "Yes", "kind": "allow_once"}]
    agent, _, _ = _recording(_permission_steps(options), permission="unknown_option")
    _assert_answered(
        agent, "perm-1", {"outcome": "selected", "optionId": UNKNOWN_PERMISSION_OPTION_ID}
    )


def test_cancelled_policy_answers_cancelled_without_sending_session_cancel():
    options = [{"optionId": "yes", "name": "Yes", "kind": "allow_once"}]
    agent, turn, _ = _recording(_permission_steps(options), permission="cancelled")
    _assert_answered(agent, "perm-1", {"outcome": "cancelled"})
    assert turn.cancelled_at_index is None
    assert not [
        e for e in agent.transcript
        if e.direction is Direction.SENT and (e.parsed or {}).get("method") == "session/cancel"
    ]
