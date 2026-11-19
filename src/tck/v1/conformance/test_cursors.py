"""Session-cursor conformance: ACP-CURSOR-001..004.

Cursors are only sent to a client that advertised `clientCapabilities.session.cursors`, which
every other connection in this suite leaves out (ACP-CLIENTCAP-009 depends on that). So the rows
share one connection that advertises `session: {cursors: {}}` and nothing else: `session/new`, two
prompt turns (the first prompt of a session has no position before it to anchor a cursor to), a
quiet period, `session/load` twice when `loadSession` is advertised, and a `session/fork` probe
with a fabricated `cursorId` when `fork` is advertised. It is made once per run and every row
judges the same traffic. Cursors are unstable and optional ("an Agent that supports cursors
announces them"), so an agent that announces none passes ACP-CURSOR-001/002 vacuously and SKIPs
ACP-CURSOR-004. ACP-CURSOR-003 is literal: it probes every agent that advertises `fork`. A turn
that outlasts `--timeout` FAILs every row, like any broken setup.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.common.plugin import capability_is_supported, register_active_process
from tck.v1.protocol import INVALID_PARAMS

from ._helpers import (
    connected_agent,
    new_session,
    quiet_period,
    run_prompt,
    skip_if_version_mismatch,
)

_FIRST_PROMPT_TEXT = "Describe the layout of this project."
_SECOND_PROMPT_TEXT = "Now suggest where to start reading the code."

_ANCHOR_ID_FIELD = {
    "user_message": "messageId",
    "agent_message": "messageId",
    "agent_thought": "messageId",
    "session_message": "messageId",
    "tool_call": "toolCallId",
    "compaction": "compactionId",
}
"""The defined anchor `type`s and the ID field naming the entity (`prompt-turn.mdx:636-645`)."""

_ENTITY_OF_UPDATE = {
    "user_message_chunk": ("user_message", "messageId"),
    "agent_message_chunk": ("agent_message", "messageId"),
    "agent_thought_chunk": ("agent_thought", "messageId"),
    "session_message": ("session_message", "messageId"),
    "session_message_chunk": ("session_message", "messageId"),
    "tool_call": ("tool_call", "toolCallId"),
    "tool_call_update": ("tool_call", "toolCallId"),
    "compaction_update": ("compaction", "compactionId"),
    "compaction_summary_chunk": ("compaction", "compactionId"),
}
"""The `session/update` kinds that report an entity an anchor can name, as `(anchor type, ID field)`."""

_CONNECTION_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one connection, in `config.stash`: `connection` once it completed, or `error` (the
exception it ended with), so every row sees the same outcome."""


@dataclass(frozen=True)
class CursorsConnection:
    transcript: list
    session_id: str
    loads: tuple[tuple[int, int], ...]
    """The `[start, end)` transcript range of each `session/load` exchange: from the request to the
    next request the TCK sent, or the end. Empty when `loadSession` is not advertised."""
    fork: tuple[int, dict | None] | None
    """`(request index, parsed response or None if it never came)` of the `session/fork` probe,
    `None` when it was not sent (no `fork` capability)."""


async def _drain(agent, seconds: float) -> None:
    try:
        await agent.wait_for_message(lambda _entry: False, timeout=seconds)
    except (AgentTimeout, AgentExited):
        pass


async def _make_connection(agent_launch, init_result, tmp_path) -> CursorsConnection:
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch, client_capabilities={"session": {"cursors": {}}}) as agent:
        register_active_process(agent)
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        await run_prompt(agent, session_id, [{"type": "text", "text": _FIRST_PROMPT_TEXT}], timeout=timeout)
        await run_prompt(agent, session_id, [{"type": "text", "text": _SECOND_PROMPT_TEXT}], timeout=timeout)
        await _drain(agent, quiet_period(timeout))
        loads: list[int] = []
        if init_result is not None and capability_is_supported(
            init_result, "agentCapabilities.loadSession", boolean=True
        ):
            for _ in range(2):
                load_id = await agent.send_request(
                    "session/load", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
                )
                loads.append(len(agent.transcript) - 1)
                try:
                    await agent.wait_for_response(load_id, timeout=timeout)
                except (AgentTimeout, AgentExited):
                    break  # ACP-LOAD-001's finding; judge the traffic seen
        fork = None
        if init_result is not None and capability_is_supported(
            init_result, "agentCapabilities.sessionCapabilities.fork"
        ):
            fork_id = await agent.send_request(
                "session/fork",
                {
                    "sessionId": session_id,
                    "cursorId": f"tck-unissued-{uuid.uuid4().hex}",
                    "cwd": str(tmp_path),
                    "mcpServers": [],
                },
            )
            probe_at = len(agent.transcript) - 1
            try:
                entry = await agent.wait_for_response(fork_id, timeout=timeout)
                fork = (probe_at, entry.parsed if isinstance(entry.parsed, dict) else {})
            except (AgentTimeout, AgentExited):
                fork = (probe_at, None)
        transcript = list(agent.transcript)
    ends = [*loads[1:], fork[0] if fork is not None else len(transcript)]
    windows = tuple(zip(loads, ends))
    return CursorsConnection(transcript, session_id, windows, fork)


async def cursors_connection(request, agent_launch, agent_initialize_result, tmp_path) -> CursorsConnection:
    """The connection described in the module docstring, made by the first row that asks and
    reused by the rest. An error or SKIP that ended it is re-raised for each row. An agent that
    did not negotiate v1 SKIPs (`VERSION-MISMATCH:`)."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    cache = request.config.stash.setdefault(_CONNECTION_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "connection" not in cache:
        try:
            cache["connection"] = await _make_connection(agent_launch, init_result, tmp_path)
        except BaseException as exc:
            cache["error"] = exc
            raise
    return cache["connection"]


def _session_events(connection: CursorsConnection) -> list[tuple[int, str, dict]]:
    """`(transcript index, sessionUpdate kind, update)` of each `session/update` for the session
    the TCK created, in wire order."""
    events = []
    for index, entry in enumerate(connection.transcript):
        msg = entry.parsed
        if entry.direction is not Direction.RECEIVED or not (
            isinstance(msg, dict) and msg.get("method") == "session/update"
        ):
            continue
        params = msg.get("params")
        if not isinstance(params, dict) or params.get("sessionId") != connection.session_id:
            continue
        update = params.get("update")
        if isinstance(update, dict) and isinstance(update.get("sessionUpdate"), str):
            events.append((index, update["sessionUpdate"], update))
    return events


def _successful_loads(connection: CursorsConnection) -> dict[int, int]:
    """The transcript index of each `session/load` request that got a success response, mapped to
    the index of that response: the session's replayed state starts afresh at the request, and
    the replay ends at the response. A failed or unanswered load rebuilds nothing."""
    loads = {}
    for start, end in connection.loads:
        request_id = connection.transcript[start].parsed.get("id")
        for index in range(start + 1, end):
            entry = connection.transcript[index]
            if entry.direction is Direction.RECEIVED and entry.matches_id(request_id):
                if isinstance(entry.parsed, dict) and "result" in entry.parsed:
                    loads[start] = index
                break
    return loads


def _walk(connection: CursorsConnection):
    """Yield `("reset", None)` at each successful `session/load` request, `("replay_end", None)`
    at its response, and `(kind, update)` for each `session/update` of the TCK's session, in wire
    order."""
    loads = _successful_loads(connection)
    marks = {start: "reset" for start in loads} | {end: "replay_end" for end in loads.values()}
    events = {index: (kind, update) for index, kind, update in _session_events(connection)}
    for index in sorted(marks.keys() | events.keys()):
        if index in marks:
            yield marks[index], None
        if index in events:
            yield events[index]


def _anchor_identity(anchor: dict) -> dict:
    return {key: value for key, value in anchor.items() if key != "_meta"}


def _anchored_entity(anchor: Any) -> tuple[str, Any] | None:
    """`(type, entity ID)` of an anchor of a defined `type`, else `None`."""
    if not isinstance(anchor, dict):
        return None
    field = _ANCHOR_ID_FIELD.get(anchor.get("type"))
    return (anchor["type"], anchor.get(field)) if field else None


def anchor_problems(connection: CursorsConnection) -> list[str]:
    """ACP-CURSOR-001's findings, in wire order. The first update seen for a `cursorId` since the
    start of the session or its last successful load must carry an object `anchor`; a later
    non-null anchor must equal it (`_meta` aside). A replayed update "carries the cursor's
    `capabilities` and `anchor`, like a first update", so the first one inside a load's replay
    needs its anchor too. After the load's response, an anchor-less update for a cursor anchored
    before the load is not judged: the agent may clear the `capabilities` of a cursor it stopped
    accepting, and such a cursor is left out of the replay."""
    anchors: dict[Any, dict] = {}
    earlier: set[Any] = set()
    in_replay = False
    problems = []
    for kind, update in _walk(connection):
        if kind == "reset":
            earlier |= anchors.keys()
            anchors, in_replay = {}, True
        elif kind == "replay_end":
            in_replay = False
        elif kind == "cursor_update" and isinstance(update.get("cursorId"), str):
            cursor_id, anchor = update["cursorId"], update.get("anchor")
            if cursor_id not in anchors:
                if isinstance(anchor, dict):
                    anchors[cursor_id] = _anchor_identity(anchor)
                elif in_replay or cursor_id not in earlier:
                    problems.append(f"first update for cursor {cursor_id!r} has no `anchor` (got {anchor!r})")
            elif isinstance(anchor, dict) and _anchor_identity(anchor) != anchors[cursor_id]:
                problems.append(
                    f"cursor {cursor_id!r} moved from {anchors[cursor_id]!r} to {_anchor_identity(anchor)!r}"
                )
    return list(dict.fromkeys(problems))


@pytest.mark.requirement("ACP-CURSOR-001")
async def test_anchor_comes_first_and_never_changes(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-001. See module docstring and `anchor_problems`."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    problems = anchor_problems(connection)
    assert not problems, "ACP-CURSOR-001: " + "; ".join(problems)


def unreported_anchor_problems(connection: CursorsConnection) -> list[str]:
    """ACP-CURSOR-002's findings, in wire order. An entity is reported by a `session/update` of
    `_ENTITY_OF_UPDATE` carrying its ID; the set starts afresh at each successful `session/load`
    (the replay re-delivers entities before their cursors). A defined-`type` anchor without its ID
    field is a schema defect, not judged here."""
    reported: set[tuple[str, Any]] = set()
    problems = []
    for kind, update in _walk(connection):
        if kind == "reset":
            reported = set()
        elif kind in _ENTITY_OF_UPDATE:
            entity_type, field = _ENTITY_OF_UPDATE[kind]
            if isinstance(update.get(field), str):
                reported.add((entity_type, update[field]))
        elif kind == "cursor_update":
            entity = _anchored_entity(update.get("anchor"))
            if entity is not None and isinstance(entity[1], str) and entity not in reported:
                problems.append(
                    f"cursor {update.get('cursorId')!r} is anchored to {entity[0]} {entity[1]!r}, "
                    "which was not reported on the session before"
                )
    return list(dict.fromkeys(problems))


@pytest.mark.requirement("ACP-CURSOR-002")
async def test_anchor_names_an_entity_already_reported(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-002. See module docstring and `unreported_anchor_problems`."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    problems = unreported_anchor_problems(connection)
    assert not problems, "ACP-CURSOR-002: " + "; ".join(problems)


@pytest.mark.requirement("ACP-CURSOR-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.fork")
async def test_fork_with_unissued_cursor_id_is_rejected(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-003. See module docstring: a fabricated `cursorId` (decision: literal, so even
    an agent that sent no cursor is probed). Only `-32602` passes. A success means the agent forked
    anyway; any other error code, or no response, is not the specified rejection."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    assert connection.fork is not None, "the fork probe was not sent although `fork` is advertised"
    _, response = connection.fork
    assert response is not None, "ACP-CURSOR-003: session/fork with an unissued `cursorId` got no response"
    error = response.get("error")
    assert isinstance(error, dict), (
        "ACP-CURSOR-003: session/fork with an unissued `cursorId` succeeded (the agent forked "
        f"anyway) instead of failing with -32602: {response!r}"
    )
    assert error.get("code") == INVALID_PARAMS, (
        f"ACP-CURSOR-003: session/fork with an unissued `cursorId` failed with code {error.get('code')!r}, "
        f"expected {INVALID_PARAMS} (Invalid params): {error!r}"
    )


def _replayed_cursor_ids(connection: CursorsConnection, window: tuple[int, int]) -> dict[tuple, tuple[str, ...]]:
    """The cursors a load replayed, keyed by `(anchor type, position, ordinal of the entity among
    the replayed entities of that type)` and valued with their `cursorId`s in order. A cursor
    whose anchored entity the replay did not report, or whose anchor is not of a defined type,
    cannot be placed and is left out."""
    start, end = window
    ordinals: dict[str, dict[Any, int]] = {}
    keyed: dict[tuple, list[str]] = {}
    for index, kind, update in _session_events(connection):
        if not start <= index < end:
            continue
        if kind in _ENTITY_OF_UPDATE:
            entity_type, field = _ENTITY_OF_UPDATE[kind]
            if isinstance(update.get(field), str):
                known = ordinals.setdefault(entity_type, {})
                known.setdefault(update[field], len(known))
        elif kind == "cursor_update" and isinstance(update.get("cursorId"), str):
            entity = _anchored_entity(update.get("anchor"))
            ordinal = ordinals.get(entity[0], {}).get(entity[1]) if entity is not None else None
            if ordinal is not None:
                key = (entity[0], update["anchor"].get("position"), ordinal)
                ids = keyed.setdefault(key, [])
                if update["cursorId"] not in ids:
                    ids.append(update["cursorId"])
    return {key: tuple(ids) for key, ids in keyed.items()}


def compared_loads(connection: CursorsConnection) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """The windows of the first two `session/load`s when both succeeded, else `None`: a failed
    load replays nothing to compare."""
    loads = _successful_loads(connection)
    windows = [window for window in connection.loads[:2] if window[0] in loads]
    return (windows[0], windows[1]) if len(windows) == 2 else None


@pytest.mark.requirement("ACP-CURSOR-004")
@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)
async def test_cursor_ids_are_stable_across_loads(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-004. Compares the cursors the two `session/load`s replayed (`_replayed_cursor_ids`).
    SKIPs when either load did not succeed (`compared_loads`), or when the first replayed none (an
    agent without cursors). Positions only one load replayed are not compared."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    windows = compared_loads(connection)
    if windows is None:
        pytest.skip("fewer than two session/load exchanges succeeded")
    first = _replayed_cursor_ids(connection, windows[0])
    if not first:
        pytest.skip("the first session/load replayed no cursor with a placeable anchor")
    second = _replayed_cursor_ids(connection, windows[1])
    changed = [
        f"{key[0]} {key[1]!r} #{key[2]}: {ids!r} then {second[key]!r}"
        for key, ids in first.items()
        if key in second and second[key] != ids
    ]
    assert not changed, "ACP-CURSOR-004: the same position got a different `cursorId` on the next load: " + "; ".join(
        changed
    )
