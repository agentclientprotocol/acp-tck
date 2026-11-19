"""Unit tests for the v1 ACP-CURSOR-001/002/004 judging over a synthetic transcript."""

from __future__ import annotations

import json
from typing import Any

from tck.common.harness import Direction, TranscriptEntry
from tck.v1.conformance.test_cursors import (
    CursorsConnection,
    _replayed_cursor_ids,
    anchor_problems,
    compared_loads,
    unreported_anchor_problems,
)

_SESSION = "s1"


def _update(update: dict[str, Any]) -> tuple[Direction, dict[str, Any]]:
    return Direction.RECEIVED, {"method": "session/update", "params": {"sessionId": _SESSION, "update": update}}


def _cursor(cursor_id: str, anchor: dict[str, Any] | None = None, **fields: Any) -> tuple[Direction, dict[str, Any]]:
    update: dict[str, Any] = {"sessionUpdate": "cursor_update", "cursorId": cursor_id, **fields}
    if anchor is not None:
        update["anchor"] = anchor
    return _update(update)


def _load(request_id: int) -> tuple[Direction, dict[str, Any]]:
    return Direction.SENT, {"id": request_id, "method": "session/load", "params": {"sessionId": _SESSION}}


def _reply(request_id: int, *, ok: bool = True) -> tuple[Direction, dict[str, Any]]:
    body = {"result": {}} if ok else {"error": {"code": -32603, "message": "load failed"}}
    return Direction.RECEIVED, {"id": request_id, **body}


_TOOL = _update({"sessionUpdate": "tool_call", "toolCallId": "t1", "title": "Read"})
_TOOL_ANCHOR = {"type": "tool_call", "toolCallId": "t1", "position": "after"}
_COMPACTION = _update({"sessionUpdate": "compaction_update", "compactionId": "k1", "status": "completed"})
_COMPACTION_ANCHOR = {"type": "compaction", "compactionId": "k1", "position": "before"}
_SESSION_MESSAGE = _update({"sessionUpdate": "session_message", "messageId": "sm1"})
_SESSION_MESSAGE_ANCHOR = {"type": "session_message", "messageId": "sm1", "position": "_tck_custom"}


def _connection(*lines: tuple[Direction, dict[str, Any]]) -> CursorsConnection:
    transcript = [
        TranscriptEntry.build(direction, json.dumps({"jsonrpc": "2.0", **message}).encode(), 0.0)
        for direction, message in lines
    ]
    starts = [index for index, (direction, message) in enumerate(lines) if message.get("method") == "session/load"]
    ends = [*starts[1:], len(transcript)]
    return CursorsConnection(transcript, _SESSION, tuple(zip(starts, ends)), None)


def test_tool_call_compaction_and_session_message_anchors_are_conforming():
    connection = _connection(
        _TOOL,
        _cursor("c1", _TOOL_ANCHOR),
        _COMPACTION,
        _cursor("c2", _COMPACTION_ANCHOR),
        _SESSION_MESSAGE,
        _cursor("c3", _SESSION_MESSAGE_ANCHOR),
        _cursor("c1", capabilities=None),  # a later update may omit the anchor
        _cursor("c2", {**_COMPACTION_ANCHOR, "_meta": {"x": 1}}),  # or repeat it, `_meta` aside
    )
    assert anchor_problems(connection) == []
    assert unreported_anchor_problems(connection) == []


def test_anchor_to_an_unreported_entity_of_each_kind_is_a_problem():
    connection = _connection(
        _cursor("c1", _TOOL_ANCHOR),
        _cursor("c2", _COMPACTION_ANCHOR),
        _cursor("c3", _SESSION_MESSAGE_ANCHOR),
    )
    problems = unreported_anchor_problems(connection)
    assert [problem.split(" is anchored to ")[1].split(",")[0] for problem in problems] == [
        "tool_call 't1'",
        "compaction 'k1'",
        "session_message 'sm1'",
    ]


def test_missing_first_anchor_and_a_moved_anchor_are_problems():
    connection = _connection(
        _TOOL,
        _cursor("c1", capabilities={}),
        _cursor("c2", _TOOL_ANCHOR),
        _cursor("c2", {**_TOOL_ANCHOR, "position": "before"}),
    )
    problems = anchor_problems(connection)
    assert len(problems) == 2
    assert problems[0].startswith("first update for cursor 'c1' has no `anchor`")
    assert problems[1].startswith("cursor 'c2' moved from")


def test_replayed_cursor_needs_its_anchor_inside_the_load():
    connection = _connection(
        _TOOL,
        _cursor("c1", _TOOL_ANCHOR),
        _load(5),
        _TOOL,
        _cursor("c1", capabilities={}),
        _reply(5),
    )
    assert anchor_problems(connection) == ["first update for cursor 'c1' has no `anchor` (got None)"]


def test_cursor_cleared_after_the_load_without_its_anchor_is_not_judged():
    """A cursor the load left out (no longer accepted) gets its `capabilities` cleared after the
    response, without an anchor: not a first update."""
    connection = _connection(
        _TOOL,
        _cursor("c1", _TOOL_ANCHOR),
        _load(5),
        _reply(5),
        _cursor("c1", capabilities=None),
        _cursor("c9", capabilities={}),  # never anchored anywhere: still a first update
    )
    assert anchor_problems(connection) == ["first update for cursor 'c9' has no `anchor` (got None)"]


def test_entities_are_forgotten_at_a_successful_load_only():
    replayed_late = _connection(
        _COMPACTION,
        _load(5),
        _cursor("c2", _COMPACTION_ANCHOR),  # before the replay re-reported the compaction
        _COMPACTION,
        _reply(5),
    )
    assert len(unreported_anchor_problems(replayed_late)) == 1
    failed_load = _connection(_COMPACTION, _load(5), _reply(5, ok=False), _cursor("c2", _COMPACTION_ANCHOR))
    assert unreported_anchor_problems(failed_load) == []


def test_two_loads_are_compared_only_when_both_succeeded():
    both = _connection(_load(5), _reply(5), _load(6), _reply(6))
    assert compared_loads(both) == ((0, 2), (2, 4))
    second_failed = _connection(_load(5), _reply(5), _load(6), _reply(6, ok=False))
    assert compared_loads(second_failed) is None
    unanswered = _connection(_load(5), _reply(5), _load(6))
    assert compared_loads(unanswered) is None


def test_replayed_cursors_are_keyed_by_type_position_and_ordinal():
    connection = _connection(
        _load(5),
        _TOOL,
        _cursor("c1", _TOOL_ANCHOR),
        _COMPACTION,
        _cursor("c2", _COMPACTION_ANCHOR),
        _SESSION_MESSAGE,
        _cursor("c3", _SESSION_MESSAGE_ANCHOR),
        _reply(5),
    )
    assert _replayed_cursor_ids(connection, connection.loads[0]) == {
        ("tool_call", "after", 0): ("c1",),
        ("compaction", "before", 0): ("c2",),
        ("session_message", "_tck_custom", 0): ("c3",),
    }
