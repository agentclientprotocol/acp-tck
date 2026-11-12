"""Patch/upsert semantics: ACP-PATCH-201, ACP-PATCH-203..212.

`ACP-PATCH-202` (the `session/prompt` result's `messageId` matches the `user_message`/
`user_message_chunk` updates' own `messageId`) is deliberately **not** registered here: it is
already fully covered by `ACP-PROMPT-201` + `ACP-PROMPT-203`.

ACP-PATCH-201/203/204/205/206/207/210 are `Tier.CAPABILITY` (`capabilities.session`);
ACP-PATCH-208/209/211/212 are `Tier.ADVISORY` with only the *test* capability-gated for the SKIP.

The tool-call rows (208, 210..212) judge every report of a tool call in wire order: a
`tool_call_update`, a `tool_call_content_chunk`, or a permission request's `tool_call` subject
(`_helpers.session_events`, `_helpers.PatchTracker`).

Most of these are pure shape checks over whatever the agent happens to emit during one driven
turn: SKIP "no <variant> observed" whenever the relevant update kind never appears, rather than a
vacuous PASS or an unjustified FAIL. Neither reference SDK exercises tool calls/plans/terminals
over v2 yet, so these rows SKIP against `testy`/`echo_agent` and only PASS for real against the
repo's own `conforming_full.py` (opted in via `emit_rich_turn_updates=True`) and its defect
fixtures.
"""

from __future__ import annotations

import base64
import os
from typing import Any

import pytest

from ._helpers import (
    FINAL_TOOL_CALL_STATUSES,
    PatchTracker,
    background_keys,
    connected_agent,
    new_session,
    permission_subject_keys,
    run_prompt,
    session_events,
    tool_call_report,
)

_PROMPT_TEXT = "hi"

_MESSAGE_KINDS = frozenset(
    {
        "user_message_chunk",
        "user_message",
        "agent_message_chunk",
        "agent_message",
        "agent_thought_chunk",
        "agent_thought",
    }
)


def _update_dicts(turn) -> list[dict[str, Any]]:
    """The inner `update` objects of `turn`'s `session/update`s for the prompted session, in wire
    order. Entity ids are unique per session (prompt-lifecycle.mdx:65-67), so a child session's
    updates must not be mixed in."""
    result: list[dict[str, Any]] = []
    for _, entry in turn.updates:
        msg = entry.parsed
        if not isinstance(msg, dict):
            continue
        params = msg.get("params")
        if not isinstance(params, dict) or params.get("sessionId") != turn.session_id:
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


@pytest.mark.requirement("ACP-PATCH-201")
@pytest.mark.capability("capabilities.session")
async def test_every_message_update_carries_a_message_id(agent_launch, tmp_path):
    """ACP-PATCH-201 (CAPABILITY). Every `*_message*`/`*_thought*` update carries a non-empty
    string `messageId` -- the keyed-upsert identity the whole message-patch family hinges on
    (`prompt-lifecycle.mdx:484`; `schema/v2/schema.unstable.json#/$defs/ContentChunk`,
    `schema/v2/schema.unstable.json#/$defs/UserMessage`,
    `schema/v2/schema.unstable.json#/$defs/AgentMessage`,
    `schema/v2/schema.unstable.json#/$defs/AgentThought`)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    message_updates = [u for u in _update_dicts(turn) if u.get("sessionUpdate") in _MESSAGE_KINDS]
    if not message_updates:
        pytest.skip("no message update observed during this turn")
    for update in message_updates:
        message_id = update.get("messageId")
        assert isinstance(message_id, str) and message_id, (
            f"{update.get('sessionUpdate')!r} update missing/empty messageId: {update!r}"
        )


@pytest.mark.requirement("ACP-PATCH-203")
@pytest.mark.capability("capabilities.session")
async def test_two_prompts_receive_distinct_message_ids(agent_launch, tmp_path):
    """ACP-PATCH-203 (CAPABILITY). Two `session/prompt`s with identical content receive two
    distinct `messageId`s (`prompt-lifecycle.mdx:368`) -- the v2 analogue of v1's
    `duplicate_session_id.py` defect pattern, applied to message ids instead of session ids."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        first = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
        second = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )

    assert first.message_id, f"first session/prompt response missing messageId: {first!r}"
    assert second.message_id, f"second session/prompt response missing messageId: {second!r}"
    assert first.message_id != second.message_id, (
        f"two session/prompt calls with identical content received the same messageId "
        f"({first.message_id!r}); each submission must get a distinct id"
    )


@pytest.mark.requirement("ACP-PATCH-204")
@pytest.mark.capability("capabilities.session")
async def test_tool_call_updates_carry_tool_call_id(agent_launch, tmp_path):
    """ACP-PATCH-204 (CAPABILITY). Every `tool_call_update` carries `toolCallId`; every
    `tool_call_content_chunk` carries `toolCallId` + `content`
    (`schema/v2/schema.unstable.json#/$defs/ToolCallUpdate`,
    `schema/v2/schema.unstable.json#/$defs/ToolCallContentChunk`) -- there is no separate "create" message in v2's
    keyed-upsert model, so the identity key must be present on every single one, including the
    very first (which *is* the create)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    updates = _update_dicts(turn)
    tool_call_updates = [u for u in updates if u.get("sessionUpdate") == "tool_call_update"]
    content_chunks = [u for u in updates if u.get("sessionUpdate") == "tool_call_content_chunk"]
    if not tool_call_updates and not content_chunks:
        pytest.skip("no tool_call_update/tool_call_content_chunk observed during this turn")
    for update in tool_call_updates:
        tool_call_id = update.get("toolCallId")
        assert isinstance(tool_call_id, str) and tool_call_id, (
            f"tool_call_update missing/empty toolCallId: {update!r}"
        )
    for update in content_chunks:
        tool_call_id = update.get("toolCallId")
        assert isinstance(tool_call_id, str) and tool_call_id, (
            f"tool_call_content_chunk missing/empty toolCallId: {update!r}"
        )
        assert update.get("content") is not None, (
            f"tool_call_content_chunk missing content: {update!r}"
        )


@pytest.mark.requirement("ACP-PATCH-205")
@pytest.mark.capability("capabilities.session")
async def test_plan_updates_carry_plan_id(agent_launch, tmp_path):
    """ACP-PATCH-205 (CAPABILITY). Every `plan_update.plan`, including an unknown/`_`-prefixed
    variant, carries `planId` (`agent-plan.mdx:147`; `schema/v2/schema.unstable.json#/$defs/PlanUpdateContent`)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    plan_updates = [u for u in _update_dicts(turn) if u.get("sessionUpdate") == "plan_update"]
    if not plan_updates:
        pytest.skip("no plan_update observed during this turn")
    for update in plan_updates:
        plan = update.get("plan")
        assert isinstance(plan, dict), f"plan_update missing plan object: {update!r}"
        plan_id = plan.get("planId")
        assert isinstance(plan_id, str) and plan_id, (
            f"plan_update.plan missing/empty planId: {update!r}"
        )


@pytest.mark.requirement("ACP-PATCH-206")
@pytest.mark.capability("capabilities.session")
async def test_terminal_updates_have_absolute_cwd(agent_launch, tmp_path):
    """ACP-PATCH-206 (CAPABILITY). Every `terminal_update` carries a `terminalId`, and a supplied
    `cwd` is absolute (`tool-calls.mdx:493-499,523-531`). `cwd` is a patch field, so a later concrete
    value may replace an earlier one."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    terminal_updates = [u for u in _update_dicts(turn) if u.get("sessionUpdate") == "terminal_update"]
    if not terminal_updates:
        pytest.skip("no terminal_update observed during this turn")
    for update in terminal_updates:
        terminal_id = update.get("terminalId")
        assert isinstance(terminal_id, str) and terminal_id, (
            f"terminal_update missing/empty terminalId: {update!r}"
        )
        cwd = update.get("cwd")
        if cwd is None:
            continue  # omitted means unchanged; null clears it
        assert isinstance(cwd, str) and os.path.isabs(cwd), (
            f"terminal_update.cwd must be an absolute path, got {cwd!r}"
        )


@pytest.mark.requirement("ACP-PATCH-207")
@pytest.mark.capability("capabilities.session")
async def test_terminal_output_chunks_decode_standalone(agent_launch, tmp_path):
    """ACP-PATCH-207 (CAPABILITY). `terminal_output_chunk.data` and `terminal_update.output.data`
    each decode as standalone RFC 4648 base64 (`tool-calls.mdx:536-537,566-570`) -- a chunk that
    only decodes once concatenated with a previous one is non-conforming."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    updates = _update_dicts(turn)
    chunks = [u for u in updates if u.get("sessionUpdate") == "terminal_output_chunk"]
    terminal_updates_with_output = [
        u
        for u in updates
        if u.get("sessionUpdate") == "terminal_update" and isinstance(u.get("output"), dict)
    ]
    if not chunks and not terminal_updates_with_output:
        pytest.skip("no terminal_output_chunk/terminal_update.output observed during this turn")
    for update in chunks:
        data = update.get("data")
        assert isinstance(data, str), f"terminal_output_chunk missing data: {update!r}"
        try:
            base64.b64decode(data, validate=True)
        except Exception as exc:  # noqa: BLE001 - report any decode failure as the assertion
            pytest.fail(f"terminal_output_chunk.data did not decode as standalone base64: {exc}")
    for update in terminal_updates_with_output:
        data = update["output"].get("data")
        assert isinstance(data, str), f"terminal_update.output missing data: {update!r}"
        try:
            base64.b64decode(data, validate=True)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"terminal_update.output.data did not decode as standalone base64: {exc}")


@pytest.mark.requirement("ACP-PATCH-208")
@pytest.mark.capability("capabilities.session")
async def test_first_tool_call_report_carries_title(agent_launch, tmp_path):
    """ACP-PATCH-208 (ADVISORY). The first report of each `toolCallId` includes a non-empty
    `title`, and `name` does not change once set (`tool-calls.mdx:41-54`). A first report may be
    a `tool_call_update`, a permission request's `tool_call` subject (tool-calls.mdx:270-273), or
    a `tool_call_content_chunk` (:198-200). A chunk carries no title, so a tool call that a chunk
    creates misses the SHOULD."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    seen: set[str] = set()
    names: dict[str, Any] = {}
    for _, kind, payload in session_events(turn):
        report = tool_call_report(kind, payload)
        if report is None:
            continue
        tool_call_id, source, fields = report
        if tool_call_id not in seen:
            seen.add(tool_call_id)
            title = fields.get("title")
            assert isinstance(title, str) and title, (
                f"the first report of toolCallId {tool_call_id!r} (a {source}) has no non-empty "
                f"title: {payload!r}"
            )
        name = fields.get("name")
        if name is None:
            continue
        previous = names.setdefault(tool_call_id, name)
        assert name == previous, (
            f"toolCallId {tool_call_id!r}'s name changed from {previous!r} to {name!r} (via a "
            f"{source})"
        )
    if not seen:
        pytest.skip("no tool call reported during this turn")


@pytest.mark.requirement("ACP-PATCH-209")
@pytest.mark.capability("capabilities.session")
async def test_requires_action_reported_around_permission_request(agent_launch, tmp_path):
    """ACP-PATCH-209 (ADVISORY). When the agent sends `session/request_permission` for the
    prompted session during the turn, it reports `requires_action` for that session at some
    point in the turn (prompt-lifecycle.mdx:153,845; tool-calls.mdx:209). A request whose
    `subject` references an item of the latest reported `background` list is for background
    work, which may leave the session `idle` (tool-calls.mdx:268; prompt-lifecycle.mdx:174), so
    it is not counted. What follows `requires_action` is `ACP-STATE-205`'s concern."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    background = None
    requests = foreground = 0
    for _, kind, payload in session_events(turn):
        if kind == "update":
            if payload.get("sessionUpdate") == "state_update":
                background = background_keys(payload)
            continue
        requests += 1
        if not (background and permission_subject_keys(payload) & background):
            foreground += 1
    if not requests:
        pytest.skip("no permission request for the prompted session observed during this turn")
    if not foreground:
        pytest.skip("every permission request observed was for listed background work")
    states = [update.get("state") for _, update in turn.states]
    assert "requires_action" in states, (
        f"agent sent session/request_permission for foreground work but never reported "
        f"state_update {{state: 'requires_action'}}; observed states: {states!r}"
    )


async def _tracked_turn(agent_launch, tmp_path):
    turn = await _drive_one_turn(agent_launch, tmp_path)
    tracker = PatchTracker()
    for _, kind, payload in session_events(turn):
        tracker.apply(kind, payload)
    return turn, tracker


@pytest.mark.requirement("ACP-PATCH-210")
@pytest.mark.capability("capabilities.session")
async def test_tool_call_status_never_regresses(agent_launch, tmp_path):
    """ACP-PATCH-210 (CAPABILITY). Per `toolCallId`, the effective status never goes back to
    `pending` and never changes once `completed`/`failed`/`cancelled` (`tool-calls.mdx:421,423`;
    `prompt-lifecycle.mdx:184`: a final tool call is not reopened). `status: null` resets it to
    `pending` (tool-calls.mdx:102-108), so it counts as a step back too."""
    _, tracker = await _tracked_turn(agent_launch, tmp_path)
    if not tracker.tool_calls:
        pytest.skip("no tool call reported during this turn")
    assert not tracker.status_violations, "; ".join(tracker.status_violations)


@pytest.mark.requirement("ACP-PATCH-211")
@pytest.mark.capability("capabilities.session")
async def test_foreground_tool_calls_are_final_at_idle(agent_launch, tmp_path):
    """ACP-PATCH-211 (ADVISORY). When the turn's idle arrives, every tool call reported during the
    turn has a final status, unless a `background` list reported during the turn named it, or the
    idle's own list names a terminal it references that has not reported `exitStatus`: tool calls
    in that list are not part of the foreground work (`tool-calls.mdx:423`), and the docs treat a
    tool call that references a listed terminal as live too (`prompt-lifecycle.mdx:216,998,1175`;
    `session-setup.mdx:391`), as Codex's command items that stay `in_progress` until the process
    exits. A terminal that exited, or left the list, no longer keeps its tool call live."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    if turn.idle_update is None:
        pytest.skip("the turn ended with an error response, not an idle")
    tracker = PatchTracker()
    listed: set[tuple[str, str]] = set()
    idle_listed: set[tuple[str, str]] = set()
    for index, kind, payload in session_events(turn):
        tracker.apply(kind, payload)
        if kind != "update" or payload.get("sessionUpdate") != "state_update":
            continue
        listed |= background_keys(payload) or set()
        if index == turn.idle_index and payload.get("state") == "idle":
            idle_listed = background_keys(payload) or set()
            break
    if not tracker.tool_calls:
        pytest.skip("no tool call reported during this turn")

    def live_terminal(terminal_id: str) -> bool:
        terminal = tracker.terminals.get(terminal_id)
        return ("terminal", terminal_id) in idle_listed and not (terminal is not None and terminal.exited)

    unfinished = {
        tool_call_id: tool_call.status
        for tool_call_id, tool_call in tracker.tool_calls.items()
        if tool_call.status not in FINAL_TOOL_CALL_STATUSES
        and ("tool_call", tool_call_id) not in listed
        and not any(live_terminal(terminal_id) for terminal_id in tool_call.terminal_ids)
    }
    assert not unfinished, (
        f"the turn's idle arrived with foreground tool calls not given a final status "
        f"(toolCallId: status): {unfinished!r}"
    )


# Named without "cancel": the CLI self-tests select the cancellation suite with `-k cancel`.
@pytest.mark.requirement("ACP-PATCH-212")
@pytest.mark.capability("capabilities.session")
async def test_capabilities_cleared_once_final(agent_launch, tmp_path):
    """ACP-PATCH-212 (ADVISORY). A tool call stops advertising `capabilities.cancel` once its
    status is final, and a terminal once it reports `exitStatus` (`tool-calls.mdx:440,600`).
    `capabilities` is a nullable patch, so a final status sent without clearing it keeps the
    old `cancel`. Passive: no `tool_call/cancel` or `terminal/cancel` is sent."""
    _, tracker = await _tracked_turn(agent_launch, tmp_path)
    if not tracker.cancel_seen:
        pytest.skip("no tool call or terminal advertised capabilities.cancel during this turn")
    assert not tracker.cancel_violations, tracker.cancel_violations[0]
