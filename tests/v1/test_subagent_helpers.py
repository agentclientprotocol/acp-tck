"""Unit tests for the subagent helpers in `tck.v1.conformance._helpers`: the announcement and
replay scoping of `child_session_traffic` and `session_content_references`, the association and
message rules, and `subagent_shape_issues`. They run on hand-built transcripts, so edge cases that
no fixture agent exercises stay covered."""

from __future__ import annotations

import json
from typing import Any

import pytest

from tck.common.harness import Direction, TranscriptEntry
from tck.v1.conformance._helpers import (
    child_config_selects,
    child_session_traffic,
    child_task_reports,
    is_absolute_path,
    session_content_references,
    session_message_streams,
    session_messages,
    subagent_shape_issues,
    subagent_updates,
)


def _entry(raw: str) -> TranscriptEntry:
    return TranscriptEntry.build(Direction.RECEIVED, raw.encode(), 0.0)


def _traffic(*messages: dict[str, Any]) -> list[TranscriptEntry]:
    return [_entry(json.dumps({"jsonrpc": "2.0", **message})) for message in messages]


def _update(session_id: str, update: dict[str, Any]) -> dict[str, Any]:
    return {"method": "session/update", "params": {"sessionId": session_id, "update": update}}


def _sub(outer: str, child: str, **fields: Any) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "subagent_update", "sessionId": child, **fields})


def _msg(outer: str, message_id: str, **fields: Any) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "session_message", "messageId": message_id, **fields})


_ANNOUNCE = _sub("p", "c")
_CHILD_CHUNK = _update("c", {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": "x"}})
_CHILD_PERMISSION = {"id": 3, "method": "session/request_permission", "params": {"sessionId": "c"}}


# --- announcement ordering (ACP-SUBAGENT-001) ---


def test_child_traffic_without_a_child_is_not_a_subagent_connection():
    children, problems = child_session_traffic(
        _traffic(_update("p", {"sessionUpdate": "agent_message_chunk"})), {"p"}
    )
    assert (children, problems) == (set(), [])


def test_child_traffic_after_its_announcement_is_conforming():
    transcript = _traffic(
        _ANNOUNCE,
        _CHILD_CHUNK,
        _CHILD_PERMISSION,
        {"id": 4, "method": "fs/read_text_file", "params": {"sessionId": "c", "path": "/a"}},
        _msg("p", "x", recipientSessionId="c"),
        _msg("c", "y", senderSessionId="p"),
        _sub("c", "g"),  # a nested child, announced on a known child
        _update("g", {"sessionUpdate": "agent_message_chunk"}),
    )
    assert child_session_traffic(transcript, {"p"}) == ({"c", "g"}, [])


@pytest.mark.parametrize(
    ("message", "mentions"),
    [
        (_CHILD_CHUNK, "agent_message_chunk"),
        (_CHILD_PERMISSION, "session/request_permission"),
        ({"id": 4, "method": "fs/read_text_file", "params": {"sessionId": "c"}}, "fs/read_text_file"),
        ({"id": 5, "method": "terminal/create", "params": {"sessionId": "c"}}, "terminal/create"),
        ({"id": 6, "method": "elicitation/create", "params": {"sessionId": "c"}}, "elicitation/create"),
        (_msg("p", "x", recipientSessionId="c"), "recipientSessionId"),
        (_msg("p", "x", senderSessionId="c"), "senderSessionId"),
    ],
)
def test_child_traffic_before_its_announcement_is_a_problem(message, mentions):
    children, problems = child_session_traffic(_traffic(message, _ANNOUNCE), {"p"})
    assert children == {"c"}
    assert len(problems) >= 1 and mentions in problems[0], problems


def test_an_announcement_on_an_unknown_session_does_not_announce():
    transcript = _traffic(_sub("stranger", "c"), _CHILD_CHUNK)
    children, problems = child_session_traffic(transcript, {"p"})
    assert children == {"stranger", "c"}
    assert len(problems) == 2


def test_child_traffic_judgement_ignores_client_lines_and_responses():
    sent = TranscriptEntry.build(Direction.SENT, json.dumps({"jsonrpc": "2.0", **_CHILD_CHUNK}).encode(), 0.0)
    reply = _entry(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"sessionId": "other"}}))
    assert child_session_traffic([sent, reply], {"p"}) == (set(), [])


# --- replay scoping: only announcements made within the `session/load` exchange count ---


def test_a_replay_is_judged_on_the_announcements_made_within_it():
    announced_live = _traffic(_ANNOUNCE, _CHILD_CHUNK)  # indexes 0-1, then the load window
    in_window = _traffic(_CHILD_CHUNK)
    # the turn announced `c`, but the load replays its chunk without re-announcing it
    children, problems = child_session_traffic(announced_live + in_window, {"p"}, (2, 3))
    assert children == {"c"} and len(problems) == 1 and "`session/load` replay" in problems[0]
    # without the scope, the carried-over announcement hides it
    assert child_session_traffic(announced_live + in_window, {"p"}) == ({"c"}, [])
    # announced again within the load: fine, and nested children follow
    window = _traffic(_ANNOUNCE, _CHILD_CHUNK, _sub("c", "g"), _update("g", {"sessionUpdate": "agent_message_chunk"}))
    assert child_session_traffic(announced_live + window, {"p"}, (2, 6)) == ({"c", "g"}, [])


def test_the_scope_covers_the_range_and_announcements_in_it_carry_on_after_it():
    transcript = _traffic(_CHILD_CHUNK, _ANNOUNCE, _CHILD_CHUNK)
    # entry 0 is outside the window (live traffic before the load: unannounced), 2 is after it
    children, problems = child_session_traffic(transcript, {"p"}, (1, 2))
    assert children == {"c"} and len(problems) == 1 and "agent_message_chunk" in problems[0]
    assert "`session/load` replay" not in problems[0]  # entry 0 is live traffic


def test_a_replayed_announcement_on_a_session_the_load_has_not_established_does_not_announce():
    live = _traffic(_ANNOUNCE, _sub("c", "g"))
    # in the load `c` is not announced again, so `g`'s announcement on `c` is not on a known session
    window = _traffic(_sub("c", "g"), _update("g", {"sessionUpdate": "agent_message_chunk"}))
    children, problems = child_session_traffic(live + window, {"p"}, (2, 4))
    assert children == {"c", "g"} and len(problems) == 2


def test_replayed_session_message_participants_are_historical_addresses():
    live = _traffic(_ANNOUNCE)
    window = _traffic(_msg("p", "m", senderSessionId="p", recipientSessionId="never-exposed"))
    # not judged and not a child: the load held it to nothing
    assert child_session_traffic(live + window, {"p"}, (1, 2)) == ({"c"}, [])
    # the same message sent live is judged
    children, problems = child_session_traffic(live + window, {"p"})
    assert children == {"c", "never-exposed"} and len(problems) == 1
    # the outer session of a replayed message must still be known to the load
    window = _traffic(_msg("c", "m", senderSessionId="p", recipientSessionId="c"))
    children, problems = child_session_traffic(live + window, {"p"}, (1, 2))
    assert children == {"c"} and len(problems) == 1


# --- `session` content references (ACP-SUBAGENT-002) ---


def _tool_update(session_id: str, update_kind: str = "tool_call_update", **fields: Any) -> dict[str, Any]:
    return _update(session_id, {"sessionUpdate": update_kind, "toolCallId": "t", **fields})


def _ref(session_id: str) -> dict[str, Any]:
    return {"type": "session", "sessionId": session_id}


def _permission(session_id: str, content: Any) -> dict[str, Any]:
    """A v1 `session/request_permission`: the tool call is the top-level `toolCall`."""
    return {
        "id": 5,
        "method": "session/request_permission",
        "params": {"sessionId": session_id, "toolCall": {"toolCallId": "t", "content": content}, "options": []},
    }


def test_session_references_without_any_are_not_a_session_content_connection():
    transcript = _traffic(_tool_update("p", content=[{"type": "content", "content": {"type": "text", "text": "x"}}]))
    assert session_content_references(transcript, {"p"}) == ([], [])


def test_session_reference_to_a_known_session_is_conforming():
    transcript = _traffic(
        _tool_update("p", "tool_call", content=[_ref("p")]),  # a client-created session
        _ANNOUNCE,
        _tool_update("p", content=[_ref("c")]),
        _permission("p", [_ref("c")]),
        _sub("c", "g"),  # a nested child, announced on a known child, then referenced
        _tool_update("c", content=[_ref("g")]),
    )
    assert session_content_references(transcript, {"p"}) == (["p", "c", "c", "g"], [])


@pytest.mark.parametrize(
    ("message", "mentions"),
    [
        (_tool_update("p", content=[_ref("c")]), "tool_call_update"),
        (_tool_update("p", "tool_call", content=[_ref("c")]), "tool_call"),
        (_permission("p", [_ref("c")]), "session/request_permission toolCall"),
    ],
)
def test_session_reference_before_its_announcement_is_a_problem(message, mentions):
    references, problems = session_content_references(_traffic(message, _ANNOUNCE), {"p"})
    assert references == ["c"]
    assert len(problems) == 1 and mentions in problems[0] and "'c'" in problems[0], problems


def test_session_reference_in_the_announcing_message_itself_is_not_yet_known():
    transcript = _traffic(_sub("p", "c", content=[_ref("c")]), _tool_update("p", content=[_ref("c")]))
    assert session_content_references(transcript, {"p"}) == (["c"], [])


def test_session_reference_after_an_announcement_on_an_unknown_session_is_a_problem():
    transcript = _traffic(_sub("stranger", "c"), _tool_update("p", content=[_ref("c")]))
    references, problems = session_content_references(transcript, {"p"})
    assert references == ["c"] and len(problems) == 1


def test_session_reference_is_not_child_traffic():
    transcript = _traffic(_tool_update("p", content=[_ref("ghost")]))
    assert child_session_traffic(transcript, {"p"}) == (set(), [])
    assert len(session_content_references(transcript, {"p"})[1]) == 1


def test_session_reference_judgement_ignores_other_content_and_malformed_items():
    transcript = _traffic(
        _tool_update("p", content=["not a dict", {"type": "session"}, {"type": "session", "sessionId": 7}, {"type": "diff"}]),
        _tool_update("p", content="not a list"),
        {"id": 5, "method": "session/request_permission", "params": {"sessionId": "p", "toolCall": "nope"}},
        _permission("p", "not a list"),
        # v2's carrier is not v1's
        {"id": 6, "method": "session/request_permission", "params": {"sessionId": "p", "subject": {"type": "tool_call", "toolCall": {"content": [_ref("ghost")]}}}},
        # a `tool_call_content_chunk` is no v1 update kind
        _tool_update("p", "tool_call_content_chunk", content=_ref("ghost")),
    )
    assert session_content_references(transcript, {"p"}) == ([], [])


def test_replayed_session_references_are_historical_addresses():
    live = _traffic(_ANNOUNCE)
    window = _traffic(_tool_update("p", content=[_ref("never-exposed")]))
    # neither judged nor counted: a load whose only reference is historical judged nothing
    assert session_content_references(live + window, {"p"}, (1, 2)) == ([], [])
    references, problems = session_content_references(live + window, {"p"})
    assert references == ["never-exposed"] and len(problems) == 1
    # a live reference after the load is judged against everything announced so far
    after = _traffic(_tool_update("p", content=[_ref("c")]))
    assert session_content_references(live + window + after, {"p"}, (1, 2)) == (["c"], [])


# --- association integrity and directories (ACP-SUBAGENT-003..006) ---


def test_no_subagent_update_is_not_a_subagent_connection():
    found = subagent_updates(_traffic(_update("p", {"sessionUpdate": "agent_message_chunk"})), {"p"})
    assert found == subagent_updates([], {"p"}) and found.updates == []
    assert not found.reported_directories


def test_a_stable_tree_with_absolute_directories_is_conforming():
    transcript = _traffic(
        _sub("p", "c", cwd="/work/c", additionalDirectories=["/work/x", "C:\\work", "\\\\srv\\share\\d"]),
        _sub("p", "c", title="again", cwd=None, additionalDirectories=[]),  # patch under the same parent
        _sub("c", "g"),
        _sub("p", "d"),
        _sub("g", "g2"),
    )
    found = subagent_updates(transcript, {"p"})
    assert found.updates == [("c", "p"), ("c", "p"), ("g", "c"), ("d", "p"), ("g2", "g")]
    assert found.reported_directories
    assert not (found.self_parented or found.client_sessions_announced or found.reparented or found.relative_paths)


def test_a_self_parent_is_judged_only_as_self_parented():
    for session in ("p", "c"):  # the client's own session, or an announced child
        found = subagent_updates(_traffic(_sub("p", "c"), _sub(session, session)), {"p"})
        assert len(found.self_parented) == 1
        assert not (found.client_sessions_announced or found.reparented)


def test_a_client_session_announced_under_another_session_is_judged_only_as_such():
    found = subagent_updates(_traffic(_sub("p", "c"), _sub("c", "p")), {"p"})
    assert len(found.client_sessions_announced) == 1 and "'p'" in found.client_sessions_announced[0]
    assert not (found.self_parented or found.reparented)


def test_a_reparented_child_is_a_problem_and_a_cycle_is_named():
    found = subagent_updates(_traffic(_sub("p", "c"), _sub("p", "d"), _sub("d", "c")), {"p"})
    assert len(found.reparented) == 1 and "cycle" not in found.reparented[0]
    assert not (found.self_parented or found.client_sessions_announced)
    cycle = subagent_updates(_traffic(_sub("p", "c"), _sub("c", "g"), _sub("g", "c")), {"p"})
    assert len(cycle.reparented) == 1 and "cycle" in cycle.reparented[0]
    longer = subagent_updates(_traffic(_sub("p", "c"), _sub("c", "g"), _sub("g", "h"), _sub("h", "c")), {"p"})
    assert len(longer.reparented) == 1 and "cycle" in longer.reparented[0]


def test_an_update_on_an_unknown_session_is_not_an_association():
    found = subagent_updates(_traffic(_sub("p", "c"), _sub("stranger", "c")), {"p"})
    assert found.reparented == []


@pytest.mark.parametrize(
    "fields",
    [
        {"cwd": "work/c"},
        {"cwd": "./c"},
        {"cwd": "file:///work/c"},
        {"cwd": ""},
        {"additionalDirectories": ["/ok", "rel"]},
        {"cwd": "C:work"},
        {"cwd": "\\work"},
    ],
)
def test_a_relative_directory_is_a_problem(fields):
    found = subagent_updates(_traffic(_sub("p", "c", **fields)), {"p"})
    assert found.reported_directories and len(found.relative_paths) == 1, found.relative_paths


@pytest.mark.parametrize(
    "fields",
    [
        {"cwd": 5},
        {"cwd": ["/a"]},
        {"additionalDirectories": "/a"},
        {"additionalDirectories": {"a": "/a"}},
        {"additionalDirectories": [5, None]},
        {"cwd": None, "additionalDirectories": []},
    ],
)
def test_a_malformed_directory_is_not_judged_here(fields):
    """A value of the wrong type is a schema defect (`ACP-SUBAGENT-015`'s): neither a relative path
    nor a reported directory, so `ACP-SUBAGENT-006` neither FAILs nor judges it."""
    found = subagent_updates(_traffic(_sub("p", "c", **fields)), {"p"})
    assert found.relative_paths == [] and not found.reported_directories


def test_is_absolute_path_accepts_native_absolute_syntaxes_only():
    assert all(
        is_absolute_path(path) for path in ("/a", "/", "C:\\a", "C:/a", "\\\\srv\\share", "\\\\srv\\share\\dir")
    )
    assert not any(is_absolute_path(path) for path in ("a", "./a", "", "C:a", "\\a", "file:///a", None, 5))


# --- `session_message` consistency (ACP-SUBAGENT-007..009) ---


def _problems(found) -> tuple[int, int, int]:
    return len(found.same_participants), len(found.foreign_outer), len(found.unlinked_views)


def test_no_session_message_is_not_a_session_message_connection():
    found = session_messages(_traffic(_update("p", {"sessionUpdate": "session_message_chunk", "messageId": "m"})), {"p"})
    assert found.count == 0 and _problems(found) == (0, 0, 0)


def test_consistent_views_in_both_directions_are_conforming():
    transcript = _traffic(
        _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in"),
        _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="out"),
        _msg("c", "ans-out", senderSessionId="c", recipientSessionId="p", recipientMessageId="ans-in"),
        _msg("p", "ans-in", senderSessionId="c", recipientSessionId="p", senderMessageId="ans-out"),
        _msg("p", "one-sided", recipientSessionId="c"),  # one participant: nothing to compare
    )
    found = session_messages(transcript, {"p"})
    assert found.count == 5 and _problems(found) == (0, 0, 0)


def test_equal_participants_are_judged_only_as_same_participants():
    for outer in ("p", "c"):
        found = session_messages(_traffic(_msg(outer, "m", senderSessionId="p", recipientSessionId="p")), {"p"})
        assert _problems(found) == (1, 0, 0), outer


def test_an_outer_session_that_is_neither_participant_is_judged_only_as_foreign_outer():
    found = session_messages(_traffic(_msg("g", "m", senderSessionId="p", recipientSessionId="c")), {"p"})
    assert _problems(found) == (0, 1, 0)
    assert _problems(session_messages(_traffic(_msg("g", "m", senderSessionId="p")), {"p"})) == (0, 0, 0)


def test_participants_are_stored_across_upserts_and_null_clears():
    split = _traffic(
        _msg("g", "m", senderSessionId="p"),
        _msg("g", "m", recipientSessionId="c"),  # now both are known: the outer session is foreign
    )
    assert _problems(session_messages(split, {"p"})) == (0, 1, 0)
    cleared = _traffic(
        _msg("g", "m", senderSessionId="p", recipientSessionId="c"),
        _msg("g", "m", recipientSessionId=None),
        _msg("g", "n", senderSessionId="p"),
    )
    assert len(session_messages(cleared, {"p"}).foreign_outer) == 1  # only the first upsert
    # the same messageId on another transcript is another message
    other = _traffic(_msg("c", "m", senderSessionId="p"), _msg("p", "m", recipientSessionId="c"))
    assert _problems(session_messages(other, {"p"})) == (0, 0, 0)
    # a malformed value clears like an unknown one
    malformed = _traffic(
        _msg("g", "m", senderSessionId="p", recipientSessionId="c"),
        _msg("g", "m", recipientSessionId=7),
    )
    assert _problems(session_messages(malformed, {"p"})) == (0, 1, 0)


def test_a_cleared_reference_is_not_judged():
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    conflicting = _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="elsewhere")
    cleared = _msg("c", "in", senderMessageId=None)
    assert _problems(session_messages(_traffic(out, conflicting), {"p"})) == (0, 0, 1)
    found = session_messages(_traffic(out, conflicting, cleared), {"p"})
    assert _problems(found) == (0, 0, 0) and found.links_judged == 0


def test_a_repeated_defective_message_is_reported_once():
    transcript = _traffic(_msg("g", "m", senderSessionId="p", recipientSessionId="c"), _msg("g", "m", content=[]))
    assert _problems(session_messages(transcript, {"p"})) == (0, 1, 0)


def test_conflicting_view_references_are_judged_only_as_unlinked_views():
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    for incoming in (
        _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="elsewhere"),
        _msg("c", "in", recipientSessionId="c", senderMessageId="elsewhere"),  # sender not repeated
    ):
        found = session_messages(_traffic(out, incoming), {"p"})
        assert _problems(found) == (0, 0, 1), found.unlinked_views
        assert "(Active RFD)" in found.unlinked_views[0]
    late = session_messages(
        _traffic(
            out,
            _msg("c", "in", senderSessionId="p", recipientSessionId="c"),
            _msg("c", "in", senderMessageId="elsewhere"),
        ),
        {"p"},
    )
    assert _problems(late) == (0, 0, 1)
    fixed = session_messages(
        _traffic(
            out,
            _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="elsewhere"),
            _msg("c", "in", senderMessageId="out"),
        ),
        {"p"},
    )
    assert _problems(fixed) == (0, 0, 0)


def test_view_links_are_judged_only_when_both_views_reference_each_other():
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    assert _problems(session_messages(_traffic(out), {"p"})) == (0, 0, 0)
    bare = _msg("c", "in", senderSessionId="p", recipientSessionId="c")
    assert _problems(session_messages(_traffic(out, bare), {"p"})) == (0, 0, 0)
    twin = _msg("c", "out", senderSessionId="p", recipientSessionId="c")  # equal IDs do not link
    assert _problems(session_messages(_traffic(out, twin), {"p"})) == (0, 0, 0)


def test_only_the_back_reference_is_compared_for_a_third_session_view():
    """The referenced view's own sender is not judged: the views do not name each other, but the
    back-reference is what the row compares, and here it is the first view's own id."""
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    third = _msg("c", "in", senderSessionId="x", recipientSessionId="c", senderMessageId="out")
    found = session_messages(_traffic(out, third), {"p"})
    assert _problems(found) == (0, 0, 0) and found.links_judged == 1
    conflicting = _msg("c", "in", senderSessionId="x", recipientSessionId="c", senderMessageId="elsewhere")
    assert _problems(session_messages(_traffic(out, conflicting), {"p"})) == (0, 0, 1)


def test_session_message_rows_count_only_what_they_judged():
    none = session_messages(_traffic(_msg("p", "m", content=[])), {"p"})
    assert (none.count, none.participants_judged, none.links_judged) == (1, 0, 0)
    one_sided = session_messages(_traffic(_msg("p", "m", senderSessionId="p", recipientMessageId="x")), {"p"})
    assert (one_sided.count, one_sided.participants_judged, one_sided.links_judged) == (1, 0, 0)
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c")
    bare_in = _msg("c", "in", senderSessionId="p", recipientSessionId="c")
    assert session_messages(_traffic(out, bare_in), {"p"}).participants_judged == 2
    assert session_messages(_traffic(out, bare_in), {"p"}).links_judged == 0
    named = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    assert session_messages(_traffic(named), {"p"}).links_judged == 0
    assert session_messages(_traffic(named, bare_in), {"p"}).links_judged == 0
    linked = _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="out")
    both = session_messages(_traffic(named, linked), {"p"})
    assert both.links_judged == 2 and both.participants_judged == 2 and _problems(both) == (0, 0, 0)
    twice = session_messages(_traffic(out, _msg("p", "out", content=[])), {"p"})
    assert twice.count == 2 and twice.participants_judged == 1


# --- delegated tasks (ACP-SUBAGENT-011, -012) ---

_TASK = _msg("c", "in", senderSessionId="p", recipientSessionId="c")
_USER = _update("c", {"sessionUpdate": "user_message_chunk", "content": {"type": "text", "text": "do it"}})


def test_a_task_session_message_before_the_output_is_conforming():
    found = child_task_reports(_traffic(_ANNOUNCE, _TASK, _CHILD_CHUNK), {"p"})
    assert (found.started, found.judged, found.user_message_tasks, found.unreported) == (1, 1, [], [])
    split = child_task_reports(
        _traffic(_ANNOUNCE, _msg("c", "in", recipientSessionId="c"), _msg("c", "in", senderSessionId="p"), _CHILD_CHUNK),
        {"p"},
    )
    assert split.unreported == []


def test_a_task_that_follows_or_misses_the_output_is_unreported():
    after = child_task_reports(_traffic(_ANNOUNCE, _CHILD_CHUNK, _TASK), {"p"})
    assert (after.started, len(after.unreported), after.user_message_tasks) == (1, 1, [])
    not_the_parent = _msg("c", "in", senderSessionId="g", recipientSessionId="c")
    assert len(child_task_reports(_traffic(_ANNOUNCE, not_the_parent, _CHILD_CHUNK), {"p"}).unreported) == 1
    assert len(child_task_reports(_traffic(_ANNOUNCE, _CHILD_CHUNK), {"p"}).unreported) == 1


def test_a_user_message_task_is_judged_only_as_a_user_message():
    found = child_task_reports(_traffic(_ANNOUNCE, _USER, _CHILD_CHUNK), {"p"})
    assert (len(found.user_message_tasks), found.unreported) == (1, [])
    assert (found.started, found.judged) == (1, 0)  # `ACP-SUBAGENT-012` has nothing to judge
    late = child_task_reports(_traffic(_ANNOUNCE, _TASK, _CHILD_CHUNK, _USER), {"p"})
    assert (late.user_message_tasks, late.unreported) == ([], [])
    quiet = child_task_reports(_traffic(_ANNOUNCE), {"p"})
    assert (quiet.started, quiet.unreported) == (0, [])


def test_task_traffic_of_an_unannounced_session_is_not_judged():
    found = child_task_reports(_traffic(_USER, _CHILD_CHUNK), {"p"})
    assert (found.started, found.user_message_tasks, found.unreported) == (0, [], [])


# --- streamed messages (ACP-SUBAGENT-013) ---


def _chunk(outer: str, message_id: str) -> dict[str, Any]:
    content = {"type": "text", "text": "more"}
    return _update(outer, {"sessionUpdate": "session_message_chunk", "messageId": message_id, "content": content})


def test_participants_before_the_first_chunk_are_conforming():
    transcript = _traffic(
        _msg("p", "m", senderSessionId="p"),
        _chunk("p", "m"),
        _chunk("p", "m"),
        _msg("p", "m", recipientSessionId="c"),
        _chunk("p", "never-named"),
    )
    found = session_message_streams(transcript, {"p"})
    assert (found.streamed, found.late_participants) == (2, [])


def test_participants_supplied_only_after_the_first_chunk_are_flagged():
    found = session_message_streams(_traffic(_chunk("p", "m"), _msg("p", "m", senderSessionId="p")), {"p"})
    assert found.streamed == 1 and len(found.late_participants) == 1
    assert "(Active RFD)" in found.late_participants[0]
    cleared = _traffic(
        _msg("p", "m", senderSessionId="p"),
        _msg("p", "m", senderSessionId=None),
        _chunk("p", "m"),
        _msg("p", "m", senderSessionId="p"),
    )
    assert len(session_message_streams(cleared, {"p"}).late_participants) == 1
    other = _traffic(_msg("c", "m", senderSessionId="p"), _chunk("p", "m"))
    assert session_message_streams(other, {"p"}).late_participants == []


# --- child configuration (ACP-SUBAGENT-014) ---


def _config(outer: str, *options: dict[str, Any]) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "config_option_update", "configOptions": list(options)})


def _select(current: str, *values: str, group: bool = False) -> dict[str, Any]:
    entries: list[dict[str, Any]] = [{"value": value, "name": value} for value in values]
    if group:
        entries = [{"group": "g", "name": "G", "options": entries}]
    return {"id": "x", "name": "X", "type": "select", "currentValue": current, "options": entries}


def test_a_child_select_with_only_its_current_value_is_conforming():
    transcript = _traffic(
        _ANNOUNCE,
        _config("c", _select("a", "a"), {"id": "b", "name": "B", "type": "boolean", "currentValue": True}),
        _config("c", _select("a", "a", group=True)),
    )
    found = child_config_selects(transcript, {"p"})
    assert (found.selects, found.with_choices) == (2, [])


def test_a_child_select_with_other_values_is_flagged():
    for option in (_select("a", "a", "b"), _select("a", "a", "b", group=True), _select("a", "b")):
        found = child_config_selects(_traffic(_ANNOUNCE, _config("c", option)), {"p"})
        assert found.selects == 1 and len(found.with_choices) == 1, option
        assert "(Active RFD)" in found.with_choices[0]


def test_a_grouped_select_counts_values_across_its_groups():
    two_groups = {
        "id": "x",
        "name": "X",
        "type": "select",
        "currentValue": "a",
        "options": [
            {"group": "g1", "name": "G1", "options": [{"value": "a", "name": "a"}]},
            {"group": "g2", "name": "G2", "options": [{"value": "b", "name": "b"}]},
        ],
    }
    found = child_config_selects(_traffic(_ANNOUNCE, _config("c", two_groups)), {"p"})
    assert found.selects == 1 and len(found.with_choices) == 1


def test_selects_of_the_clients_own_or_an_unannounced_session_are_not_judged():
    transcript = _traffic(_config("p", _select("a", "a", "b")), _config("c", _select("a", "a", "b")))
    assert child_config_selects(transcript, {"p"}).selects == 0


# --- schema validity of the subagent parts only (ACP-SUBAGENT-015) ---


def test_valid_subagent_messages_are_conforming():
    transcript = _traffic(
        _sub("p", "c", state={"state": "running"}, cwd="/work"),
        _msg("p", "m", senderSessionId="p", recipientSessionId="c", content=[{"type": "text", "text": "hi"}]),
        _chunk("p", "m"),
        _tool_update("p", status="completed", kind="other", title="spawn", content=[_ref("c")]),
        _permission("c", [_ref("g")]),
    )
    assert subagent_shape_issues(transcript) == (5, [])


@pytest.mark.parametrize(
    "message",
    [
        _sub("p", "c", state={"stopReason": "end_turn"}),
        _sub("p", "c", state="running"),
        _sub("p", "c", additionalDirectories="/a"),
        _msg("p", "m", messageId=7),
        _update("p", {"sessionUpdate": "session_message", "senderSessionId": "p"}),
        _update("p", {"sessionUpdate": "session_message_chunk", "messageId": "m"}),
    ],
)
def test_a_malformed_subagent_update_is_a_problem(message):
    judged, problems = subagent_shape_issues(_traffic(message))
    assert judged == 1 and len(problems) >= 1, problems


def test_a_malformed_session_item_is_a_problem_wherever_it_is_carried():
    bad = {"type": "session", "sessionId": 7}
    for message in (_tool_update("p", content=[bad]), _permission("p", [bad])):
        judged, problems = subagent_shape_issues(_traffic(message))
        assert judged == 1 and len(problems) >= 1 and "content[0]" in problems[0], problems


def test_a_defect_outside_the_subagent_parts_is_not_judged_here():
    """The rest of a tool call or permission request, and the notification around a subagent
    update, belong to the rows that judge those messages (`ACP-PROMPT-002`, `ACP-SCHEMA-001`)."""
    transcript = _traffic(
        _tool_update("p", status="bogus", content=[_ref("c")]),
        _tool_update("p", kind="bogus", content=[_ref("c")]),
        {
            "id": 5,
            "method": "session/request_permission",
            "params": {
                "sessionId": "p",
                "toolCall": {"toolCallId": "t", "status": "bogus", "content": [_ref("c")]},
                "options": [{"optionId": 1}],
            },
        },
        # an invalid outer session ID on a valid subagent update
        {"method": "session/update", "params": {"sessionId": 7, "update": {"sessionUpdate": "subagent_update", "sessionId": "c"}}},
    )
    judged, problems = subagent_shape_issues(transcript)
    assert (judged, problems) == (4, [])


def test_subagent_shape_judgement_ignores_other_messages():
    transcript = _traffic(
        _update("p", {"sessionUpdate": "agent_message_chunk"}),
        _tool_update("p", content=[{"type": "diff"}]),
        _tool_update("p", content="not a list"),
        _permission("p", "not a list"),
        {"id": 6, "method": "fs/read_text_file", "params": {"sessionId": "p"}},
    )
    reply = _entry(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}))
    assert subagent_shape_issues([*transcript, reply]) == (0, [])
