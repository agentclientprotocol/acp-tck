"""Open-enum emitter rules: ACP-ENUM-201, ACP-ENUM-203.

v2's schema is open at every scalar enum and tagged-union discriminator except
`ElicitationSchemaType` and the JSON-RPC `jsonrpc` literal -- but prose still binds the
*emitter*: a value must be a defined constant OR begin with `_`.
`tck.v2.protocol.is_valid_open_enum_value` is the hand-written check that enforces this
(the schema itself would happily accept `"kind": "sorcery"` via its own `other`-branch
fallback). The defined-constant sets themselves (`TOOL_KIND`, `TOOL_CALL_STATUS`,
`PLAN_ENTRY_PRIORITY`, `PLAN_ENTRY_STATUS`, `SESSION_UPDATE_KIND`, `STATE_UPDATE_STATE`,
`TOOL_CALL_CONTENT_TYPE`, `PERMISSION_OPTION_KIND`) live in `tck.v2.protocol` next to `STOP_REASONS`, not here -- see
`tests/v2/test_validation.py::test_enum_sets_match_the_schema` for the meta-test that keeps them
honest against `schema.unstable.json`.

The re-worded v1 `ACP-PROMPT-001` ("the idle's `stopReason` is a defined constant or `_`-prefixed")
is deliberately **not** re-registered here: it is already fully covered by `ACP-STATE-203`, which
already combines "carries a `stopReason`" with exactly this value-legality check.

`ACP-ENUM-201` applies the extensibility rule ("extensions MUST NOT define custom non-underscore
values", extensibility.mdx:226-231) to every open-enum site observable in one turn: the
`sessionUpdate` discriminator, `state_update.state`, `tool_call_update.kind`/`.status`, tool-call
content `type`, plan entries' `priority`/`status`, and `session/request_permission` options'
`kind` (only if the agent asks for permission). Turn-observable, so `Tier.CAPABILITY`,
`capability="capabilities.session"` per the session-baseline tiering rule.

`ACP-ENUM-203` is the receiver-tolerance direction (client sends a `_`-prefixed value, agent must
not crash/`-32602`): receivers MUST accept unknown discriminator values where the schema has a
fallback (extensibility.mdx:49-53), so `Tier.CAPABILITY`, `capability="capabilities.session"`.
`run_prompt()` has no hook to inject a non-standard permission-outcome value, so this test drives
its own minimal turn by hand instead of reusing it.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout
from tck.v2.protocol import (
    METHOD_NOT_FOUND,
    PERMISSION_OPTION_KIND,
    PLAN_ENTRY_PRIORITY,
    PLAN_ENTRY_STATUS,
    SESSION_UPDATE_KIND,
    STATE_UPDATE_STATE,
    TOOL_CALL_CONTENT_TYPE,
    TOOL_CALL_STATUS,
    TOOL_KIND,
    is_valid_open_enum_value,
)

from ._helpers import connected_agent, new_session, run_prompt

_PROMPT_TEXT = "hi"


def _update_dicts(turn) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for _, entry in turn.updates:
        msg = entry.parsed
        if not isinstance(msg, dict):
            continue
        params = msg.get("params")
        if not isinstance(params, dict):
            continue
        update = params.get("update")
        if isinstance(update, dict):
            result.append(update)
    return result


async def _drive_one_turn(agent_launch, tmp_path):
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
    return turn


@pytest.mark.requirement("ACP-ENUM-201")
@pytest.mark.capability("capabilities.session")
async def test_open_enum_sites_are_defined_or_underscore_prefixed(agent_launch, tmp_path):
    """ACP-ENUM-201 (CAPABILITY). Across one driven turn, every value at an open-enum site is a
    defined constant or begins with `_`: `sessionUpdate`, `state_update.state`,
    `tool_call_update.kind`/`.status`, tool-call content `type`, plan entries' `priority`/`status`,
    and permission options' `kind`. Permission requests are only scanned if the agent sends
    one; the test never requires it."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    updates = _update_dicts(turn)

    checked = 0
    violations: list[str] = []

    def check(label: str, value: Any, defined: frozenset[str]) -> None:
        nonlocal checked
        checked += 1
        if not is_valid_open_enum_value(value, defined):
            violations.append(f"{label}={value!r}")

    for update in updates:
        kind = update.get("sessionUpdate")
        if kind is None:
            continue
        check("sessionUpdate", kind, SESSION_UPDATE_KIND)
        if kind == "state_update" and "state" in update:
            check("state_update.state", update["state"], STATE_UPDATE_STATE)
        if kind == "tool_call_update":
            if update.get("kind") is not None:
                check("tool_call_update.kind", update["kind"], TOOL_KIND)
            if update.get("status") is not None:
                check("tool_call_update.status", update["status"], TOOL_CALL_STATUS)
        if kind in ("tool_call_update", "tool_call_content_chunk"):
            for block in update.get("content") or []:
                if isinstance(block, dict) and "type" in block:
                    check("tool call content type", block["type"], TOOL_CALL_CONTENT_TYPE)
        if kind == "plan_update" and isinstance(update.get("plan"), dict):
            for entry in update["plan"].get("entries") or []:
                if not isinstance(entry, dict):
                    continue
                if "priority" in entry:
                    check("plan entry priority", entry["priority"], PLAN_ENTRY_PRIORITY)
                if "status" in entry:
                    check("plan entry status", entry["status"], PLAN_ENTRY_STATUS)

    for request in turn.client_requests_seen:
        msg = request.parsed
        if not isinstance(msg, dict) or msg.get("method") != "session/request_permission":
            continue
        params = msg.get("params")
        options = params.get("options") if isinstance(params, dict) else None
        for option in options if isinstance(options, list) else []:
            if isinstance(option, dict) and "kind" in option:
                check("permission option kind", option["kind"], PERMISSION_OPTION_KIND)

    if checked == 0:
        pytest.skip("no open-enum value observed during this turn")
    assert not violations, (
        f"open-enum value(s) that are neither a defined constant nor `_`-prefixed: {violations!r}"
    )


@pytest.mark.requirement("ACP-ENUM-203")
@pytest.mark.capability("capabilities.session")
async def test_agent_tolerates_underscore_prefixed_permission_outcome(agent_launch, tmp_path):
    """ACP-ENUM-203 (CAPABILITY, `capabilities.session`). Answers a `session/request_permission`
    with a `_`-prefixed, non-standard `outcome`
    value instead of `selected`/`cancelled`; the agent must not crash or answer the *prompt*
    itself with `-32602` (Invalid params) -- it may treat the unrecognised outcome however it
    likes internally (untestable, B4/B6), but the connection and the turn must survive it.

    `run_prompt()` always answers with `selected`/`cancelled`, with no hook to override the
    outcome value, so this drives a minimal turn by hand instead."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        prompt_id = await agent.send_request(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": _PROMPT_TEXT}]},
        )

        permission_seen = False
        prompt_response = None
        crashed_or_invalid = None
        reached_idle = False
        active_seen = False

        crashed_break = False

        async def _process_message(msg: dict[str, Any]) -> None:
            nonlocal permission_seen, prompt_response, crashed_or_invalid, reached_idle
            nonlocal active_seen, crashed_break

            if entry.matches_id(prompt_id):
                prompt_response = msg
                error = msg.get("error")
                if isinstance(error, dict) and error.get("code") == -32602:
                    crashed_or_invalid = error
                    crashed_break = True
                return

            method = msg.get("method")
            if method == "session/request_permission" and "id" in msg:
                permission_seen = True
                await agent.send_message(
                    {
                        "jsonrpc": "2.0",
                        "id": msg["id"],
                        "result": {"outcome": {"outcome": "_tck/unknown"}},
                    }
                )
                return

            if method == "session/update":
                params = msg.get("params") or {}
                update = params.get("update") if isinstance(params, dict) else None
                if isinstance(update, dict) and update.get("sessionUpdate") == "state_update":
                    # An idle ends the turn once an active state (`running`/`requires_action`)
                    # was seen, with or without a stopReason; `unknown` and custom states never
                    # end it. Fallback for an agent that reports no active state: an idle
                    # carrying a stopReason after the permission was answered.
                    state = update.get("state")
                    if state in ("running", "requires_action"):
                        active_seen = True
                    elif state == "idle" and (
                        active_seen or (permission_seen and update.get("stopReason") is not None)
                    ):
                        reached_idle = True
                return

            if method is not None and "id" in msg:
                await agent.send_message(
                    {
                        "jsonrpc": "2.0",
                        "id": msg["id"],
                        "error": {"code": METHOD_NOT_FOUND, "message": "Method not found"},
                    }
                )

        # `deadline` bounds the whole loop, not each read -- otherwise an agent that keeps
        # streaming updates without ever reaching idle could run this loop forever.
        loop = asyncio.get_running_loop()
        deadline = loop.time() + agent_launch.default_timeout
        try:
            while not reached_idle and not crashed_break:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise AgentTimeout(
                        "never reached a terminating idle state_update after a `_`-prefixed "
                        f"permission outcome within {agent_launch.default_timeout}s",
                        agent.transcript,
                        stderr=agent.stderr_text(),
                    )
                entry = await agent.read_line(timeout=remaining)
                raw = entry.parsed
                # A line may be a JSON-RPC batch array (`ACP-BATCH-207` permits a spontaneous
                # batch of `session/update` notifications) -- unwrap it like
                # `_helpers.run_prompt`'s `_handle_one` does so a batching agent isn't
                # penalized just because its terminating idle arrived inside a batch.
                if isinstance(raw, list):
                    items = [item for item in raw if isinstance(item, dict)]
                elif isinstance(raw, dict):
                    items = [raw]
                else:
                    continue
                for msg in items:
                    entry = replace(entry, parsed=msg)
                    await _process_message(msg)
                    if reached_idle or crashed_break:
                        break
        except (AgentTimeout, AgentExited):
            pass  # judged below: absence of a crash signal is not itself proof of tolerance

    if not permission_seen:
        pytest.skip("no permission request observed during this turn")
    assert crashed_or_invalid is None, (
        f"agent answered the prompt with -32602 after receiving a `_`-prefixed, non-standard "
        f"permission outcome: {crashed_or_invalid!r}"
    )
    assert reached_idle, (
        f"agent never reached a terminating idle state_update after a `_`-prefixed permission "
        f"outcome was returned; last prompt response seen: {prompt_response!r}"
    )
