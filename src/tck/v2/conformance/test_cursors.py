"""Session-cursor conformance: ACP-CURSOR-001..004.

v2 has no client capability for cursors ("No Client capability is required in v2"), so the rows
share one connection that advertises nothing: `session/new`, two prompt turns, a quiet period (a
cursor may follow the turn's idle), two `session/resume`s of the same session with
`replayFrom: {"type": "start"}` (a full replay each, the windows of ACP-CURSOR-001, -002 and -004),
and a `session/fork` probe with a fabricated `cursorId` when `fork` is advertised. It is made once
per run and every row judges the same traffic. Cursors are unstable and optional ("An Agent that
supports cursors announces them"), so an agent that announces none SKIPs ACP-CURSOR-001, -002 and
-004. ACP-CURSOR-003 is literal: it probes every agent that advertises `fork`. A turn that
outlasts `--timeout` FAILs every row, like any broken setup.

The state of ACP-CURSOR-001 and -002 starts afresh at each successful resume request, since the
replay re-delivers entities before the cursors anchored to them. ACP-CURSOR-001 demands a replayed
anchor only inside the replay, up to `replay_complete` (or the response); ACP-CURSOR-004 compares
each resume's traffic up to the next request.

The connection's mock client answers any agent -> client request with `-32601`, as everywhere.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.v2.protocol import INVALID_PARAMS

from ._helpers import (
    connected_agent,
    drain_quiet,
    iter_messages,
    new_session,
    quiet_period,
    resume_session,
    run_prompt,
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
"""The defined anchor `type`s and the ID field naming the entity (`prompt-lifecycle.mdx:968-975`)."""

_ENTITY_OF_UPDATE = {
    "user_message": ("user_message", "messageId"),
    "user_message_chunk": ("user_message", "messageId"),
    "agent_message": ("agent_message", "messageId"),
    "agent_message_chunk": ("agent_message", "messageId"),
    "agent_thought": ("agent_thought", "messageId"),
    "agent_thought_chunk": ("agent_thought", "messageId"),
    "session_message": ("session_message", "messageId"),
    "session_message_chunk": ("session_message", "messageId"),
    "tool_call_update": ("tool_call", "toolCallId"),
    "tool_call_content_chunk": ("tool_call", "toolCallId"),
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
    resumes: tuple[tuple[int, int, bool], ...]
    """`(request index, end index, succeeded)` of each full-replay `session/resume`: the end is the
    next request the TCK sent, or the end of the transcript."""
    fork: tuple[int, dict | None] | None
    """`(request index, parsed response or None if it never came)` of the `session/fork` probe,
    `None` when it was not sent (no `fork` capability)."""


def _request_index(transcript: list, start: int, method: str) -> int:
    """The index of the first request of `method` the TCK sent at or after `start`."""
    for index in range(start, len(transcript)):
        entry = transcript[index]
        if (
            entry.direction is Direction.SENT
            and isinstance(entry.parsed, dict)
            and entry.parsed.get("method") == method
        ):
            return index
    return start


async def _make_connection(agent_launch, init_result, tmp_path) -> CursorsConnection:
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        await run_prompt(agent, session_id, [{"type": "text", "text": _FIRST_PROMPT_TEXT}], timeout=timeout)
        await run_prompt(agent, session_id, [{"type": "text", "text": _SECOND_PROMPT_TEXT}], timeout=timeout)
        await drain_quiet(agent, quiet_period(timeout))
        starts: list[tuple[int, bool]] = []
        for _ in range(2):
            before = len(agent.transcript)
            try:
                response, _updates = await resume_session(
                    agent, session_id, tmp_path, replay_from={"type": "start"}, timeout=timeout
                )
            except (AgentTimeout, AgentExited):
                starts.append((_request_index(agent.transcript, before, "session/resume"), False))
                break  # the resume rows' finding; judge the traffic seen
            parsed = response.parsed
            starts.append(
                (
                    _request_index(agent.transcript, before, "session/resume"),
                    isinstance(parsed, dict) and "result" in parsed,
                )
            )
        fork = None
        capabilities = init_result.get("capabilities") if isinstance(init_result, dict) else None
        session_caps = capabilities.get("session") if isinstance(capabilities, dict) else None
        if isinstance(session_caps, dict) and session_caps.get("fork") not in (None, False):
            fork_id = await agent.send_request(
                "session/fork",
                {"sessionId": session_id, "cursorId": f"tck-unissued-{uuid.uuid4().hex}", "cwd": str(tmp_path)},
            )
            probe_at = _request_index(agent.transcript, len(agent.transcript) - 1, "session/fork")
            try:
                entry = await agent.wait_for_response(fork_id, timeout=timeout)
                fork = (probe_at, entry.parsed if isinstance(entry.parsed, dict) else {})
            except (AgentTimeout, AgentExited):
                fork = (probe_at, None)
        transcript = list(agent.transcript)
    ends = [index for index, _ in starts[1:]] + [fork[0] if fork is not None else len(transcript)]
    resumes = tuple((start, end, ok) for (start, ok), end in zip(starts, ends))
    return CursorsConnection(transcript, session_id, resumes, fork)


async def cursors_connection(request, agent_launch, agent_initialize_result, tmp_path) -> CursorsConnection:
    """The connection described in the module docstring, made by the first row that asks and
    reused by the rest. An error or SKIP that ended it is re-raised for each row."""
    cache = request.config.stash.setdefault(_CONNECTION_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "connection" not in cache:
        try:
            cache["connection"] = await _make_connection(agent_launch, agent_initialize_result.result, tmp_path)
        except BaseException as exc:
            cache["error"] = exc
            raise
    return cache["connection"]


def _replay_end(connection: CursorsConnection, start: int, end: int) -> int:
    """The index just past the replay of the resume requested at `start`: past its
    `replay_complete` on the session, else at its response, else `end`."""
    request_id = connection.transcript[start].parsed.get("id")
    for index in range(start + 1, end):
        entry = connection.transcript[index]
        if entry.direction is not Direction.RECEIVED:
            continue
        if entry.matches_id(request_id):
            return index
        for message in iter_messages(entry):
            params = message.get("params")
            update = params.get("update") if isinstance(params, dict) else None
            if (
                message.get("method") == "session/update"
                and params.get("sessionId") == connection.session_id
                and isinstance(update, dict)
                and update.get("sessionUpdate") == "replay_complete"
            ):
                return index + 1
    return end


def _walk(connection: CursorsConnection):
    """Yield `("reset", None)` at each successful full-replay `session/resume` request,
    `("replay_end", None)` where its replay ends (`_replay_end`), and `(kind, update)` for each
    `session/update` of the TCK's session, in wire order."""
    resets = {start for start, _end, ok in connection.resumes if ok}
    replay_ends = {_replay_end(connection, start, end) for start, end, ok in connection.resumes if ok}
    for index, entry in enumerate(connection.transcript):
        if index in replay_ends:
            yield "replay_end", None
        if index in resets:
            yield "reset", None
        if entry.direction is not Direction.RECEIVED:
            continue
        for message in iter_messages(entry):
            params = message.get("params")
            if message.get("method") != "session/update" or not isinstance(params, dict):
                continue
            update = params.get("update")
            if (
                params.get("sessionId") == connection.session_id
                and isinstance(update, dict)
                and isinstance(update.get("sessionUpdate"), str)
            ):
                yield update["sessionUpdate"], update
    if len(connection.transcript) in replay_ends:
        yield "replay_end", None


def _skip_if_no_cursor(connection: CursorsConnection) -> None:
    if not any(kind == "cursor_update" for kind, _ in _walk(connection)):
        pytest.skip("the agent sent no cursor_update")


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
    start of the session or its last successful full replay must carry an object `anchor` (a
    replayed update "carries the cursor's `capabilities` and `anchor`, like a first update"); a
    later non-null anchor must equal it (`_meta` aside). After a replay ends, an anchor-less update
    for a cursor anchored before it is not judged: the agent may clear the `capabilities` of a
    cursor it stopped accepting, and such a cursor is left out of the replay."""
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
@pytest.mark.capability("capabilities.session")
async def test_anchor_comes_first_and_never_changes(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-001. See module docstring and `anchor_problems`."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    _skip_if_no_cursor(connection)
    problems = anchor_problems(connection)
    assert not problems, "ACP-CURSOR-001: " + "; ".join(problems)


def unreported_anchor_problems(connection: CursorsConnection) -> list[str]:
    """ACP-CURSOR-002's findings, in wire order. An entity is reported by a `session/update` of
    `_ENTITY_OF_UPDATE` carrying its ID; the set starts afresh at each successful full-replay resume
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
@pytest.mark.capability("capabilities.session")
async def test_anchor_names_an_entity_already_reported(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-002. See module docstring and `unreported_anchor_problems`."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    _skip_if_no_cursor(connection)
    problems = unreported_anchor_problems(connection)
    assert not problems, "ACP-CURSOR-002: " + "; ".join(problems)


@pytest.mark.requirement("ACP-CURSOR-003")
@pytest.mark.capability("capabilities.session.fork")
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


def _replayed_cursors(connection: CursorsConnection, window: tuple[int, int]) -> dict[str, tuple[str, ...]]:
    """The cursors a replay delivered, keyed by their anchor (`type`, entity ID, `position`) and
    valued with their `cursorId`s in order. A cursor with no object anchor is left out."""
    start, end = window
    keyed: dict[str, list[str]] = {}
    for index in range(start, end):
        entry = connection.transcript[index]
        if entry.direction is not Direction.RECEIVED:
            continue
        for message in iter_messages(entry):
            params = message.get("params")
            update = params.get("update") if isinstance(params, dict) else None
            if (
                message.get("method") == "session/update"
                and isinstance(params, dict)
                and params.get("sessionId") == connection.session_id
                and isinstance(update, dict)
                and update.get("sessionUpdate") == "cursor_update"
                and isinstance(update.get("cursorId"), str)
                and isinstance(update.get("anchor"), dict)
            ):
                key = repr(sorted(_anchor_identity(update["anchor"]).items()))
                ids = keyed.setdefault(key, [])
                if update["cursorId"] not in ids:
                    ids.append(update["cursorId"])
    return {key: tuple(ids) for key, ids in keyed.items()}


@pytest.mark.requirement("ACP-CURSOR-004")
@pytest.mark.capability("capabilities.session")
async def test_cursor_ids_are_stable_across_replays(request, agent_launch, agent_initialize_result, tmp_path):
    """ACP-CURSOR-004. Compares the cursors the two full-replay resumes delivered
    (`_replayed_cursors`). SKIPs when fewer than two resumes succeeded or no anchor appears in both
    replays (an agent without cursors, or one whose anchors changed across the replay, which the
    spec allows)."""
    connection = await cursors_connection(request, agent_launch, agent_initialize_result, tmp_path)
    if len(connection.resumes) < 2 or not all(ok for _, _, ok in connection.resumes):
        pytest.skip("fewer than two full-replay session/resume exchanges succeeded")
    first = _replayed_cursors(connection, connection.resumes[0][:2])
    second = _replayed_cursors(connection, connection.resumes[1][:2])
    shared = first.keys() & second.keys()
    if not shared:
        pytest.skip("no cursor anchor appears in both replays")
    changed = [f"anchor {key}: {first[key]!r} then {second[key]!r}" for key in sorted(shared) if first[key] != second[key]]
    assert not changed, "ACP-CURSOR-004: the same anchor got a different `cursorId` on the next replay: " + "; ".join(
        changed
    )
