"""Background-work conformance: ACP-STATE-206..209, ACP-INFO-BACKGROUND-201/202.

`running`/`requires_action`/`idle`/`unknown` state updates may carry a `background` snapshot of
work running independently of foreground work (prompt-lifecycle.mdx:188-210). Each test drives
one prompt turn on a fresh session, drains a quiet period for the background traffic that may
follow the idle, and judges the session's `session/update`s in wire order. The TCK cannot make an
agent start background work, so every row here SKIPs for an agent that never reports a list.
`ACP-INFO-BACKGROUND-202` drives a cancelled turn instead and only records what it saw.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import Direction

from ._helpers import (
    BACKGROUND_ID_FIELDS,
    PatchTracker,
    background_keys,
    connected_agent,
    drain_quiet,
    iter_messages,
    new_session,
    quiet_period,
    run_prompt,
    session_events,
)

_PROMPT_TEXT = "hi"

# The states that carry `background` (prompt-lifecycle.mdx:188). A custom state's shape is its
# own, so it is not judged.
_BACKGROUND_STATES = frozenset({"running", "requires_action", "idle", "unknown"})

# Each item type's announcing `sessionUpdate` (prompt-lifecycle.mdx:206).
_ANNOUNCING_UPDATE = {
    "terminal": "terminal_update",
    "tool_call": "tool_call_update",
    "subagent": "subagent_update",
}

_FINAL_TOOL_CALL_STATUSES = frozenset({"completed", "failed", "cancelled"})


async def _session_updates(agent_launch, tmp_path) -> list[dict[str, Any]]:
    """Every `update` the agent sent for the prompted session over one turn plus a quiet drain
    after it, in wire order."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        await run_prompt(agent, session_id, [{"type": "text", "text": _PROMPT_TEXT}], timeout=timeout)
        await drain_quiet(agent, quiet_period(timeout))
        updates = []
        for entry in agent.transcript:
            if entry.direction is not Direction.RECEIVED:
                continue
            for msg in iter_messages(entry):
                params = msg.get("params")
                if (
                    msg.get("method") == "session/update"
                    and isinstance(params, dict)
                    and params.get("sessionId") == session_id
                    and isinstance(params.get("update"), dict)
                ):
                    updates.append(params["update"])
        return updates


def _is_background_state(update: dict[str, Any]) -> bool:
    return update.get("sessionUpdate") == "state_update" and update.get("state") in _BACKGROUND_STATES


def _key_of(update: dict[str, Any]) -> tuple[str, str] | None:
    """The `background` key an announcing update is about, or `None`."""
    for item_type, kind in _ANNOUNCING_UPDATE.items():
        if update.get("sessionUpdate") == kind:
            item_id = update.get(BACKGROUND_ID_FIELDS[item_type])
            return (item_type, item_id) if isinstance(item_id, str) else None
    return None


def _is_final(update: dict[str, Any]) -> bool:
    kind = update.get("sessionUpdate")
    if kind == "tool_call_update":
        return update.get("status") in _FINAL_TOOL_CALL_STATUSES
    return kind == "terminal_update" and update.get("exitStatus") is not None


@pytest.mark.requirement("ACP-STATE-206")
@pytest.mark.capability("capabilities.session")
async def test_background_list_is_kept_once_reported(agent_launch, tmp_path):
    """ACP-STATE-206. Once a state update for the session carries a `background` array, every
    later `running`/`requires_action`/`idle`/`unknown` update for it carries one too. Omitted
    and `null` both mean "not reported" (prompt-lifecycle.mdx:204). SKIPs when no list is
    reported."""
    updates = await _session_updates(agent_launch, tmp_path)
    reported = False
    for update in updates:
        if not _is_background_state(update):
            continue
        if isinstance(update.get("background"), list):
            reported = True
        elif reported:
            pytest.fail(
                "a state_update omitted `background` (or sent it as a non-array) after the "
                f"session had reported a background list: {update!r}"
            )
    if not reported:
        pytest.skip("no background list reported for this session")


@pytest.mark.requirement("ACP-STATE-207")
@pytest.mark.capability("capabilities.session")
async def test_background_items_are_announced_before_they_are_listed(agent_launch, tmp_path):
    """ACP-STATE-207. Every `terminal`/`tool_call`/`subagent` item in a `background` list was
    announced earlier for the session by a `terminal_update`/`tool_call_update`/
    `subagent_update` carrying its id (prompt-lifecycle.mdx:206). Items of other types are not
    judged (:209). SKIPs when no such item is listed."""
    updates = await _session_updates(agent_launch, tmp_path)
    announced: set[tuple[str, str]] = set()
    listed = False
    for update in updates:
        key = _key_of(update)
        if key is not None:
            announced.add(key)
        if not _is_background_state(update):
            continue
        keys = background_keys(update) or set()
        listed = listed or bool(keys)
        unannounced = keys - announced
        assert not unannounced, (
            f"background list names {sorted(unannounced)!r}, never announced earlier for this "
            f"session by a terminal_update/tool_call_update/subagent_update: {update!r}"
        )
    if not listed:
        pytest.skip("no terminal/tool_call/subagent item listed in a background snapshot")


@pytest.mark.requirement("ACP-STATE-208")
@pytest.mark.capability("capabilities.session")
async def test_background_items_are_finalized_before_idle_removal(
    agent_launch, tmp_path, record_property
):
    """ACP-STATE-208. A `terminal`/`tool_call` item that an `idle` snapshot drops from the
    previous `background` list had its `exitStatus` or final tool-call status reported first
    (prompt-lifecycle.mdx:206). A removal in an active snapshot is only recorded: foreground work
    that waits on an item takes it off the list unfinished (:208). Subagents are not judged: no
    finalization is defined for them. SKIPs when no idle snapshot removes such an item."""
    updates = await _session_updates(agent_launch, tmp_path)
    finalized: set[tuple[str, str]] = set()
    previous: set[tuple[str, str]] | None = None
    judged = False
    unjudged: list[str] = []
    for update in updates:
        key = _key_of(update)
        if key is not None and _is_final(update):
            finalized.add(key)
        if not _is_background_state(update):
            continue
        keys = background_keys(update)
        if keys is None:
            continue
        removed = {k for k in (previous or set()) - keys if k[0] != "subagent"}
        previous = keys
        if not removed:
            continue
        if update.get("state") != "idle":
            unjudged.extend(f"{t}:{i}" for t, i in sorted(removed))
            continue
        judged = True
        unfinished = removed - finalized
        assert not unfinished, (
            f"an idle background snapshot removed {sorted(unfinished)!r} before a "
            "terminal_update with exitStatus or a final tool_call_update status was sent "
            f"for it: {update!r}"
        )
    if unjudged:
        record_property("acp_tck_unjudged_background_removals", unjudged)
    if not judged:
        pytest.skip("no idle background snapshot removed a terminal/tool_call item")


@pytest.mark.requirement("ACP-STATE-209")
@pytest.mark.capability("capabilities.session")
async def test_background_list_is_resent_when_work_ends_while_idle(agent_launch, tmp_path):
    """ACP-STATE-209 (ADVISORY). When a listed `terminal`/`tool_call` item reaches its final
    status while the session is `idle`, a later `state_update` drops it from the list
    (prompt-lifecycle.mdx:205). Only an end while idle is judged: during active work the next
    snapshot follows anyway. The start half is not judged: an item announced but not yet listed
    cannot be told from foreground work. SKIPs when no listed item ends while idle."""
    updates = await _session_updates(agent_launch, tmp_path)
    state: Any = None
    listed: set[tuple[str, str]] = set()
    unresent: set[tuple[str, str]] = set()
    judged = False
    for update in updates:
        key = _key_of(update)
        if key is not None and _is_final(update) and state == "idle" and key in listed:
            unresent.add(key)
            judged = True
        if update.get("sessionUpdate") != "state_update":
            continue
        state = update.get("state")
        if not _is_background_state(update):
            continue
        keys = background_keys(update)
        if keys is None:
            listed = set()
            continue
        listed = keys
        unresent &= keys
    if not judged:
        pytest.skip("no listed terminal/tool_call item reached its final status while idle")
    assert not unresent, (
        f"{sorted(unresent)!r} reached its final status while the session was idle and was never "
        "dropped from the background list by a later state_update"
    )


@pytest.mark.requirement("ACP-INFO-BACKGROUND-201")
@pytest.mark.capability("capabilities.session")
async def test_listed_tool_call_with_its_terminal_is_recorded(
    agent_launch, tmp_path, record_property
):
    """ACP-INFO-BACKGROUND-201 (INFORMATIONAL). Records the tool calls that a `background` list
    names together with a terminal they reference in `terminal` content. Process-backed work is
    listed as its terminal only, and the Agent MUST NOT also list a tool call whose only live
    work is that terminal (prompt-lifecycle.mdx:208). The client cannot tell whether such a
    tool call has other live work, so nothing is asserted. SKIPs when no list is reported."""
    updates = await _session_updates(agent_launch, tmp_path)
    tracker = PatchTracker()
    reported = False
    both: set[str] = set()
    for update in updates:
        tracker.apply("update", update)
        keys = background_keys(update) if _is_background_state(update) else None
        if keys is None:
            continue
        reported = True
        for item_type, item_id in keys:
            tool_call = tracker.tool_calls.get(item_id) if item_type == "tool_call" else None
            if tool_call is not None and any(("terminal", t) in keys for t in tool_call.terminal_ids):
                both.add(item_id)
    if not reported:
        pytest.skip("no background list reported for this session")
    record_property("acp_tck_listed_tool_calls_with_listed_terminal", sorted(both))


@pytest.mark.requirement("ACP-INFO-BACKGROUND-202")
@pytest.mark.capability("capabilities.session")
async def test_listed_work_after_interrupting_the_turn_is_recorded(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-INFO-BACKGROUND-202 (INFORMATIONAL). When `session/cancel` is sent while the latest
    `background` list is non-empty, records which listed items reached a final status before the
    cancelled turn's idle and which the idle still lists. `session/cancel` does not cover work
    in the list (prompt-lifecycle.mdx:1173), but listed work may also end on its own, so nothing
    is asserted. SKIPs when the cancel did not land or no list was reported."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_cancel=True,
            timeout=timeout,
        )
    cancel_index = turn.cancelled_at_index
    if cancel_index is None:
        pytest.skip("cancellation not exercised: session/cancel was not sent")
    listed: set[tuple[str, str]] = set()
    finalized: set[tuple[str, str]] = set()
    at_idle: set[tuple[str, str]] | None = None
    for index, kind, payload in session_events(turn):
        if kind != "update":
            continue
        if index < cancel_index:
            if _is_background_state(payload):
                listed = background_keys(payload) or set()
            continue
        key = _key_of(payload)
        if key is not None and key in listed and _is_final(payload):
            finalized.add(key)
        if _is_background_state(payload) and (keys := background_keys(payload)) is not None:
            at_idle = listed & keys
    if not listed:
        pytest.skip("no background work was listed when session/cancel was sent")
    record_property("acp_tck_background_listed_at_cancel", sorted(listed))
    record_property("acp_tck_background_finalized_after_cancel", sorted(finalized))
    record_property(
        "acp_tck_background_listed_at_idle",
        "no list reported after session/cancel" if at_idle is None else sorted(at_idle),
    )
