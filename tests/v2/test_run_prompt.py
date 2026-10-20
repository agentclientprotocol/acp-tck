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

from tck.common.harness import AgentLaunch, AgentProcess, Direction
from tck.v2.conformance._helpers import run_prompt

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


def test_permission_answer_prefers_an_allow_option():
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


def test_hold_permission_cancels_before_answering_cancelled():
    options = [{"optionId": "yes", "name": "Yes", "kind": "allow_once"}]
    agent, turn = _drive(
        [_RESPONSE, _state("running"), _state("requires_action"), _permission_request(options),
         {"wait_method": "session/cancel"}, {"wait_id": "perm-1"},
         _state("idle", stopReason="cancelled")],
        on_cancel=True,
        hold_permission=True,
    )
    assert turn.held_permission is not None
    assert turn.state_at_cancel == "requires_action"
    assert turn.stop_reason == "cancelled"
    answer_index, answer = _sent_answer(agent, "perm-1")
    assert answer["result"]["outcome"] == {"outcome": "cancelled"}
    assert turn.cancelled_at_index is not None and turn.cancelled_at_index < answer_index
