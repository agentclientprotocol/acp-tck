"""Unit tests for `tck.v2.conformance._helpers.run_prompt`'s turn-end predicate and permission
handling, driven against a tiny scripted stdio agent.

The script replays a JSON plan once it reads `session/prompt`: each step is a message to write
(`"$ID"` stands for the prompt's request id), `{"sleep": s}`, `{"wait_method": m}` (read until
a message with that method arrives) or `{"wait_id": i}` (read until the response to `i`).
`"pre"` steps are written at startup, before any prompt.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import pytest

from tck.common.harness import AgentLaunch, AgentProcess, AgentTimeout, Direction
from tck.common.plugin import _TEST_PROPERTIES
from tck.v2.conformance._helpers import (
    UNKNOWN_PERMISSION_OPTION_ID,
    permission_outcome,
    run_prompt,
)

_SCRIPT = r"""
import json, sys, time
plan = json.loads(sys.argv[1])
def out(m):
    sys.stdout.write(json.dumps(m) + "\n"); sys.stdout.flush()
def read_until(pred):
    for line in sys.stdin:
        m = json.loads(line)
        if pred(m):
            return m
    sys.exit(0)
for step in plan.get("pre", []):
    out(step)
prompt = read_until(lambda m: m.get("method") == "session/prompt")
for step in plan["steps"]:
    if "sleep" in step:
        time.sleep(step["sleep"])
    elif "wait_method" in step:
        read_until(lambda m, w=step["wait_method"]: m.get("method") == w)
    elif "wait_id" in step:
        read_until(lambda m, w=step["wait_id"]: "method" not in m and m.get("id") == w)
    else:
        out(json.loads(json.dumps(step).replace('"$ID"', json.dumps(prompt["id"]))))
for line in sys.stdin:
    pass
"""

_SESSION = "s1"
_RESPONSE = {"jsonrpc": "2.0", "id": "$ID", "result": {"messageId": "m1"}}
_ERROR = {"jsonrpc": "2.0", "id": "$ID", "error": {"code": -32603, "message": "boom"}}


def _update(update: dict[str, Any], session_id: str = _SESSION) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": "session/update",
        "params": {"sessionId": session_id, "update": update},
    }


def _state(state: str, session_id: str = _SESSION, **extra: Any) -> dict[str, Any]:
    return _update({"sessionUpdate": "state_update", "state": state, **extra}, session_id)


def _drive(steps: list[dict[str, Any]], *, pre: list[dict[str, Any]] | None = None, **kwargs: Any):
    async def go():
        plan = json.dumps({"pre": pre or [], "steps": steps})
        launch = AgentLaunch(
            command=[sys.executable, "-c", _SCRIPT, plan], startup_timeout=2.0, default_timeout=2.0
        )
        async with AgentProcess(launch) as agent:
            for _ in pre or []:
                await agent.read_line(timeout=2.0)
            turn = await run_prompt(
                agent, _SESSION, [{"type": "text", "text": "hi"}], timeout=3.0, **kwargs
            )
            return agent, turn

    return asyncio.run(go())


def test_stale_idle_snapshot_before_running_does_not_end_the_turn():
    _, turn = _drive(
        [_RESPONSE, _state("idle", stopReason="end_turn"), {"sleep": 0.2}, _state("running"),
         _state("idle", stopReason="max_tokens")]
    )
    assert turn.terminated_by == "idle"
    assert turn.stop_reason == "max_tokens"
    assert [update["state"] for _, update in turn.states] == ["idle", "running", "idle"]


def test_idle_after_requires_action_ends_the_turn_without_a_stop_reason():
    _, turn = _drive([_RESPONSE, _state("requires_action"), _state("idle")])
    assert turn.terminated_by == "idle"
    assert turn.stop_reason is None
    assert turn.active_seen and turn.requires_action_seen


def test_error_response_after_active_work_waits_for_the_idle():
    _, turn = _drive(
        [_state("running"), _ERROR, {"sleep": 0.3}, _state("idle", stopReason="error")]
    )
    assert "error" in turn.response_entry.parsed
    assert turn.terminated_by == "idle"
    assert turn.stop_reason == "error"


def test_error_response_without_active_work_ends_the_turn():
    _, turn = _drive([_ERROR])
    assert turn.terminated_by == "error"
    assert turn.idle_update is None


def test_stop_reason_idle_without_active_state_is_the_confirmed_fallback():
    _, turn = _drive([_RESPONSE, _state("idle", stopReason="end_turn")])
    assert turn.terminated_by == "idle_without_active"
    assert turn.stop_reason == "end_turn"
    assert not turn.active_seen


def test_unknown_state_is_not_active():
    _, turn = _drive([_RESPONSE, _state("unknown"), _state("idle", stopReason="end_turn")])
    assert turn.terminated_by == "idle_without_active"


def test_child_session_states_do_not_end_the_parent_turn():
    _, turn = _drive(
        [_RESPONSE, _state("running"), _state("running", "child"),
         _state("idle", "child", stopReason="end_turn"), {"sleep": 0.2},
         _state("idle", stopReason="refusal")]
    )
    assert turn.stop_reason == "refusal"
    assert [update["state"] for _, update in turn.states] == ["running", "idle"]


def test_last_known_active_state_seeds_the_turn():
    _, turn = _drive([_RESPONSE, _state("idle")], pre=[_state("running")])
    assert turn.terminated_by == "idle"
    assert turn.active_seen


def _sent_answer(agent, request_id: str) -> tuple[int, dict[str, Any]]:
    for index, entry in enumerate(agent.transcript):
        msg = entry.parsed
        if entry.direction is Direction.SENT and isinstance(msg, dict) and msg.get("id") == request_id:
            return index, msg
    raise AssertionError(f"no answer sent for {request_id!r}")


def _permission_request(options: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": "perm-1",
        "method": "session/request_permission",
        "params": {"sessionId": _SESSION, "title": "ok?", "options": options},
    }


def test_permission_answer_falls_back_to_allow_always_when_no_allow_once():
    options = [
        {"optionId": "no", "name": "No", "kind": "reject_once"},
        {"optionId": "yes", "name": "Yes", "kind": "allow_always"},
    ]
    agent, _ = _drive(
        [_RESPONSE, _state("running"), _permission_request(options), {"wait_id": "perm-1"},
         _state("idle", stopReason="end_turn")]
    )
    _, answer = _sent_answer(agent, "perm-1")
    assert answer["result"]["outcome"] == {"outcome": "selected", "optionId": "yes"}


_HELD_PREFIX = [_RESPONSE, _state("running"), _state("requires_action")]
_CANCEL_REQUEST = {"jsonrpc": "2.0", "method": "$/cancel_request", "params": {"requestId": "perm-1"}}
_ALLOW_ONCE = [{"optionId": "yes", "name": "Yes", "kind": "allow_once"}]


def _hold(steps: list[dict[str, Any]]):
    return _drive(
        [*_HELD_PREFIX, _permission_request(_ALLOW_ONCE), {"wait_method": "session/cancel"}, *steps],
        on_cancel=True,
        hold_permission=True,
    )


def test_hold_permission_leaves_the_request_unanswered_until_the_turn_ends():
    agent, turn = _hold([_state("idle", stopReason="cancelled")])
    assert turn.held_permission is not None
    assert turn.state_at_cancel == "requires_action"
    assert turn.stop_reason == "cancelled"
    assert turn.held_answered_on == "turn_end"
    assert turn.held_cancel_request_index is None
    answer_index, answer = _sent_answer(agent, "perm-1")
    assert answer["result"]["outcome"] == {"outcome": "cancelled"}
    assert turn.cancelled_at_index < turn.idle_index < answer_index


def test_hold_permission_answers_a_withdrawn_request_cancelled():
    agent, turn = _hold(
        [_CANCEL_REQUEST, {"wait_id": "perm-1"}, _state("idle", stopReason="cancelled")]
    )
    assert turn.held_answered_on == "cancel_request"
    answer_index, answer = _sent_answer(agent, "perm-1")
    assert answer["result"]["outcome"] == {"outcome": "cancelled"}
    assert turn.cancelled_at_index < turn.held_cancel_request_index < answer_index < turn.idle_index


def test_hold_permission_sees_a_withdrawal_that_follows_the_idle():
    _, turn = _hold([_state("idle", stopReason="cancelled"), {"sleep": 0.1}, _CANCEL_REQUEST])
    assert turn.held_answered_on == "cancel_request"
    assert turn.held_cancel_request_index > turn.idle_index


def test_hold_permission_answers_at_the_deadline_and_records_it():
    agent, turn = _hold([{"wait_id": "perm-1"}, _state("idle", stopReason="cancelled")])
    assert turn.held_answered_on == "timeout"
    assert turn.stop_reason == "cancelled"
    answer_index, _ = _sent_answer(agent, "perm-1")
    assert answer_index < turn.idle_index


def test_hold_permission_times_out_when_the_turn_never_ends_even_once_answered():
    with pytest.raises(AgentTimeout, match="not even after its held session/request_permission"):
        _hold([{"wait_id": "perm-1"}])


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


def _recording(**kwargs: Any):
    """Run `_drive` with a per-test property list in scope; returns (agent, turn, properties)."""
    props: list[tuple[str, object]] = []
    token = _TEST_PROPERTIES.set(props)
    try:
        agent, turn = _drive(**kwargs)
    finally:
        _TEST_PROPERTIES.reset(token)
    return agent, turn, props


def test_default_policy_selects_allow_once_not_the_first_option():
    options = [
        {"optionId": "always", "name": "Always", "kind": "allow_always"},
        {"optionId": "once", "name": "Once", "kind": "allow_once"},
    ]
    agent, turn, props = _recording(steps=_permission_steps(options))
    _assert_answered(agent, "perm-1", {"outcome": "selected", "optionId": "once"})
    assert turn.permission_fallbacks == []
    assert props == []


def test_allow_always_fallback_is_recorded_on_the_turn_and_the_report_property():
    options = [
        {"optionId": "no", "name": "No", "kind": "reject_once"},
        {"optionId": "always", "name": "Always", "kind": "allow_always"},
    ]
    agent, turn, props = _recording(steps=_permission_steps(options))
    _assert_answered(agent, "perm-1", {"outcome": "selected", "optionId": "always"})
    note = "allow_always selected (allow_once not offered)"
    assert turn.permission_fallbacks == [note]
    assert props == [("acp_tck_permission_fallback", note)]


def test_reject_once_policy_selects_the_reject_option():
    options = [
        {"optionId": "yes", "name": "Yes", "kind": "allow_once"},
        {"optionId": "no", "name": "No", "kind": "reject_once"},
    ]
    agent, _, _ = _recording(steps=_permission_steps(options), permission="reject_once")
    _assert_answered(agent, "perm-1", {"outcome": "selected", "optionId": "no"})


def test_reject_once_without_a_reject_option_cancels_the_turn_instead_of_selecting_any_option():
    options = [
        {"optionId": "always", "name": "Always", "kind": "allow_always"},
        {"optionId": "once", "name": "Once", "kind": "allow_once"},
    ]
    agent, turn, props = _recording(
        steps=[_RESPONSE, _state("running"), _permission_request(options),
               {"wait_method": "session/cancel"}, {"wait_id": "perm-1"},
               _state("idle", stopReason="cancelled")],
        permission="reject_once",
    )
    answer_index, answer = _sent_answer(agent, "perm-1")
    assert answer["result"]["outcome"] == {"outcome": "cancelled"}
    cancels = [
        i for i, e in enumerate(agent.transcript)
        if e.direction is Direction.SENT and (e.parsed or {}).get("method") == "session/cancel"
    ]
    assert len(cancels) == 1 and cancels[0] < answer_index
    assert agent.transcript[cancels[0]].parsed["params"] == {"sessionId": _SESSION}
    assert turn.cancelled_at_index == cancels[0]
    assert turn.terminated_by == "idle" and turn.stop_reason == "cancelled"
    note = "agent offered no reject_once option"
    assert turn.permission_cancels == [note]
    assert turn.permission_fallbacks == []
    assert props == [("acp_tck_permission_fallback", note)]


def test_unknown_option_policy_selects_an_unoffered_id():
    options = [{"optionId": "yes", "name": "Yes", "kind": "allow_once"}]
    agent, _, _ = _recording(steps=_permission_steps(options), permission="unknown_option")
    _assert_answered(
        agent, "perm-1", {"outcome": "selected", "optionId": UNKNOWN_PERMISSION_OPTION_ID}
    )


def test_cancelled_policy_answers_cancelled_without_sending_session_cancel():
    options = [{"optionId": "yes", "name": "Yes", "kind": "allow_once"}]
    agent, turn, _ = _recording(steps=_permission_steps(options), permission="cancelled")
    _assert_answered(agent, "perm-1", {"outcome": "cancelled"})
    assert turn.cancelled_at_index is None
    assert not [
        e for e in agent.transcript
        if e.direction is Direction.SENT and (e.parsed or {}).get("method") == "session/cancel"
    ]


def _permission_steps(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_RESPONSE, _state("running"), _permission_request(options), {"wait_id": "perm-1"},
            _state("idle", stopReason="end_turn")]
