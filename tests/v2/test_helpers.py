"""Unit tests for the line classifiers, the `session/list` resume route and the tool-call patch
tracker in `tck.v2.conformance._helpers`."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from tck.common.harness import Direction, TranscriptEntry
from tck.v2.conformance._helpers import (
    child_config_selects,
    child_state_mirrors,
    child_task_reports,
    session_message_streams,
    _LIST_ROUTE_MAX_PAGES,
    PatchTracker,
    _route_from_list,
    agent_requests,
    assert_unknown_session_error,
    child_session_traffic,
    is_absolute_path,
    is_agent_initiated,
    is_response_line,
    session_content_references,
    session_messages,
    subagent_updates,
    tool_call_report,
)

_NOTE = '{"jsonrpc":"2.0","method":"_x/status"}'
_REQUEST = '{"jsonrpc":"2.0","id":7,"method":"session/request_permission"}'
_REPLY = '{"jsonrpc":"2.0","id":1,"result":{}}'


def _entry(raw: str) -> TranscriptEntry:
    return TranscriptEntry.build(Direction.RECEIVED, raw.encode(), 0.0)


@pytest.mark.parametrize(
    ("raw", "agent_initiated", "response"),
    [
        (_NOTE, True, False),
        (_REQUEST, True, False),
        (f"[{_NOTE},{_NOTE}]", False, False),  # an array is never agent-initiated (no batches)
        (_REPLY, False, True),
        (f"[{_REPLY},{_REPLY}]", False, True),  # a reply array: flattened for is_response_line
        (f"[{_NOTE},{_REPLY}]", False, True),  # mixed: judged as a reply, never skipped
        ("[]", False, False),
        (f"[{_NOTE},17]", False, False),
        ("{not json", False, False),
        ("17", False, False),
    ],
)
def test_line_classification(raw: str, agent_initiated: bool, response: bool) -> None:
    entry = _entry(raw)
    assert is_agent_initiated(entry) is agent_initiated
    assert is_response_line(entry) is response


def test_agent_requests_are_received_objects_with_method_and_id():
    sent = TranscriptEntry.build(Direction.SENT, _REQUEST.encode(), 0.0)
    null_id = '{"jsonrpc":"2.0","id":null,"method":"session/request_permission"}'
    transcript = [
        sent,  # a client request is never an agent request
        _entry(_NOTE),
        _entry(_REPLY),
        _entry(_REQUEST),
        _entry(null_id),  # still a request: the caller judges its id
        _entry(f"[{_REQUEST}]"),  # an array is non-conformant but its elements are still read
    ]
    assert [m["id"] for m in agent_requests(transcript)] == [7, None, 7]


class _ListAgent:
    """Stub agent answering `session/list` from scripted pages, recording each request."""

    def __init__(self, pages: list[dict[str, object]]) -> None:
        self._pages = iter(pages)
        self.list_params: list[dict[str, object]] = []
        self.methods: list[str] = []

    async def send_request(self, method: str, params: dict[str, object] | None = None) -> int:
        self.methods.append(method)
        if method == "session/list":
            self.list_params.append(params or {})
        return len(self.methods)

    async def wait_for_response(self, req_id: int, timeout: float | None = None) -> TranscriptEntry:
        raw = json.dumps({"jsonrpc": "2.0", "id": req_id, "result": next(self._pages)})
        return _entry(raw)


def _info(session_id: str, cwd: str) -> dict[str, str]:
    return {"sessionId": session_id, "cwd": cwd}


def _from_list(agent: _ListAgent, cwd: Path) -> str:
    return asyncio.run(_route_from_list(agent, cwd, 1.0))  # type: ignore[arg-type]


def test_list_route_skips_foreign_cwd_and_picks_own_session(tmp_path: Path) -> None:
    agent = _ListAgent(
        [{"sessions": [_info("operator", "/operator/saved-project"), _info("mine", str(tmp_path))]}]
    )
    assert _from_list(agent, tmp_path) == "mine"
    assert agent.list_params == [{"cwd": str(tmp_path)}]  # asks the agent to filter too


def test_list_route_accepts_symlinked_spelling_of_own_cwd(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    agent = _ListAgent([{"sessions": [_info("mine", str(link))]}])
    assert _from_list(agent, real) == "mine"


def test_list_route_follows_next_cursor(tmp_path: Path) -> None:
    agent = _ListAgent(
        [
            {"sessions": [_info("operator", "/operator/saved-project")], "nextCursor": "p2"},
            {"sessions": [_info("mine", str(tmp_path))]},
        ]
    )
    assert _from_list(agent, tmp_path) == "mine"
    assert [p.get("cursor") for p in agent.list_params] == [None, "p2"]


def test_list_route_rejects_when_only_foreign_or_relative_cwds_listed(tmp_path: Path) -> None:
    agent = _ListAgent(
        [{"sessions": [_info("operator", "/operator/saved-project"), _info("rel", tmp_path.name)]}]
    )
    with pytest.raises(RuntimeError, match="no session created in the TCK's own cwd"):
        _from_list(agent, tmp_path)
    assert agent.methods == ["session/list"]  # nothing is ever resumed or prompted


def test_list_route_gives_up_after_page_bound(tmp_path: Path) -> None:
    agent = _ListAgent([{"sessions": [], "nextCursor": f"p{i}"} for i in range(50)])
    with pytest.raises(RuntimeError):
        _from_list(agent, tmp_path)
    assert len(agent.list_params) == _LIST_ROUTE_MAX_PAGES


def _error_entry(code: int | None, data: object = None, *, session_id: str = "s1") -> TranscriptEntry:
    error: dict = {"code": code, "message": "Resource not found"}
    if data is not None:
        error["data"] = data
    return _entry(json.dumps({"jsonrpc": "2.0", "id": 1, "error": error}))


def test_unknown_session_error_accepts_the_conforming_shape() -> None:
    assert_unknown_session_error(_error_entry(-32002, {"sessionId": "s1"}), "session/prompt", "s1")


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        (_error_entry(-32602, {"sessionId": "s1"}), "expected code -32002, got -32602"),
        (_error_entry(-32002), "expected error.data to be an object"),
        (_error_entry(-32002, {"sessionId": "other"}), "expected data.sessionId='s1', got 'other'"),
        (_error_entry(-32002, {}), "expected data.sessionId='s1', got None"),
        (_entry(_REPLY), "did not return an error"),
    ],
)
def test_unknown_session_error_rejects_every_deviation(entry: TranscriptEntry, expected: str) -> None:
    with pytest.raises(AssertionError, match=expected):
        assert_unknown_session_error(entry, "session/prompt", "s1")


def test_unknown_session_error_reports_code_and_data_problems_together() -> None:
    with pytest.raises(AssertionError) as excinfo:
        assert_unknown_session_error(_error_entry(-32602), "session/resume", "s1")
    message = str(excinfo.value)
    assert "expected code -32002" in message and "expected error.data" in message


def _tool_call(tool_call_id: str = "t1", **fields: Any) -> tuple[str, dict[str, Any]]:
    return "update", {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id, **fields}


def _tracked(*events: tuple[str, dict[str, Any]]) -> PatchTracker:
    tracker = PatchTracker()
    for kind, payload in events:
        tracker.apply(kind, payload)
    return tracker


def test_tool_call_report_covers_updates_chunks_and_tool_call_subjects() -> None:
    chunk = {"sessionUpdate": "tool_call_content_chunk", "toolCallId": "t1", "content": {"type": "content"}}
    assert tool_call_report("update", chunk) == ("t1", "tool_call_content_chunk", {})
    subject = {"subject": {"type": "tool_call", "toolCall": {"toolCallId": "t2", "title": "x"}}}
    assert tool_call_report("permission", subject) == (
        "t2", "permission subject", {"toolCallId": "t2", "title": "x"}
    )
    assert tool_call_report("permission", {"subject": {"type": "command", "toolCallId": "t3"}}) is None
    assert tool_call_report(*_tool_call("")) is None
    assert tool_call_report("update", {"sessionUpdate": "plan_update"}) is None


def test_status_moving_forward_is_not_a_violation() -> None:
    tracker = _tracked(
        _tool_call(status="pending"),
        _tool_call(status="in_progress"),
        _tool_call(status="paused"),
        _tool_call(status="in_progress"),
        _tool_call(title="unchanged status"),
        _tool_call(status="completed"),
        _tool_call(status="completed"),  # a repeat is not a change
    )
    assert tracker.status_violations == []
    assert tracker.tool_calls["t1"].status == "completed"


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        ([_tool_call(status="in_progress"), _tool_call(status="pending")], "went back"),
        ([_tool_call(status="in_progress"), _tool_call(status=None)], "went back"),  # null = pending
        ([_tool_call(status="completed"), _tool_call(status="in_progress")], "changed from final"),
        ([_tool_call(status="cancelled"), _tool_call(status="completed")], "changed from final"),
        (
            [
                _tool_call(status="failed"),
                (
                    "permission",
                    {"subject": {"type": "tool_call", "toolCall": {"toolCallId": "t1", "status": "in_progress"}}},
                ),
            ],
            "permission subject",
        ),
    ],
)
def test_status_regressions_are_collected(events, expected: str) -> None:
    tracker = _tracked(*events)
    assert len(tracker.status_violations) == 1 and expected in tracker.status_violations[0]


def test_a_chunk_creates_a_pending_tool_call() -> None:
    chunk = {"sessionUpdate": "tool_call_content_chunk", "toolCallId": "t1", "content": {}}
    tracker = _tracked(("update", chunk))
    assert tracker.tool_calls["t1"].status == "pending"


def test_cancel_cleared_with_the_final_status_is_not_a_violation() -> None:
    tracker = _tracked(
        _tool_call(status="in_progress", capabilities={"cancel": {}}),
        _tool_call(status="completed", capabilities=None),
        ("update", {"sessionUpdate": "terminal_update", "terminalId": "x", "capabilities": {"cancel": {}}}),
        ("update", {"sessionUpdate": "terminal_update", "terminalId": "x", "exitStatus": {}, "capabilities": {}}),
    )
    assert tracker.cancel_seen
    assert tracker.cancel_violations == []


@pytest.mark.parametrize(
    "events",
    [
        [_tool_call(status="in_progress", capabilities={"cancel": {}}), _tool_call(status="failed")],
        [_tool_call(status="completed", capabilities={"cancel": {}})],
        [
            ("update", {"sessionUpdate": "terminal_update", "terminalId": "x", "capabilities": {"cancel": {}}}),
            ("update", {"sessionUpdate": "terminal_output_chunk", "terminalId": "x", "data": ""}),
            ("update", {"sessionUpdate": "terminal_update", "terminalId": "x", "exitStatus": {"exitCode": 1}}),
        ],
    ],
)
def test_cancel_kept_after_final_is_a_violation(events) -> None:
    tracker = _tracked(*events)
    assert tracker.cancel_violations


def test_a_malformed_or_null_cancel_advertises_nothing() -> None:
    tracker = _tracked(
        _tool_call(status="completed", capabilities={"cancel": None}),
        _tool_call("t2", status="completed", capabilities="bogus"),
    )
    assert not tracker.cancel_seen and tracker.cancel_violations == []


def _traffic(*messages: dict[str, Any]) -> list[TranscriptEntry]:
    return [_entry(json.dumps({"jsonrpc": "2.0", **message})) for message in messages]


def _update(session_id: str, update: dict[str, Any]) -> dict[str, Any]:
    return {"method": "session/update", "params": {"sessionId": session_id, "update": update}}


_ANNOUNCE = _update("p", {"sessionUpdate": "subagent_update", "sessionId": "c"})
_CHILD_CHUNK = _update("c", {"sessionUpdate": "agent_message_chunk", "messageId": "m"})
_CHILD_PERMISSION = {"id": 3, "method": "session/request_permission", "params": {"sessionId": "c"}}


def test_child_traffic_without_a_child_is_not_a_subagent_connection():
    children, problems = child_session_traffic(
        _traffic(_update("p", {"sessionUpdate": "agent_message_chunk", "messageId": "m"})), {"p"}
    )
    assert (children, problems) == (set(), [])


def test_child_traffic_after_its_announcement_is_conforming():
    transcript = _traffic(
        _ANNOUNCE,
        _CHILD_CHUNK,
        _CHILD_PERMISSION,
        _update("p", {"sessionUpdate": "session_message", "messageId": "x", "recipientSessionId": "c"}),
        _update("c", {"sessionUpdate": "session_message", "messageId": "y", "senderSessionId": "p"}),
        # a nested child, announced on a known child
        _update("c", {"sessionUpdate": "subagent_update", "sessionId": "g"}),
        _update("g", {"sessionUpdate": "agent_message_chunk", "messageId": "m"}),
    )
    assert child_session_traffic(transcript, {"p"}) == ({"c", "g"}, [])


@pytest.mark.parametrize(
    ("message", "mentions"),
    [
        (_CHILD_CHUNK, "agent_message_chunk"),
        (_CHILD_PERMISSION, "session/request_permission"),
        (
            {"id": 4, "method": "elicitation/create", "params": {"sessionId": "c", "message": "?"}},
            "elicitation/create",
        ),
        (
            _update("p", {"sessionUpdate": "session_message", "messageId": "x", "recipientSessionId": "c"}),
            "recipientSessionId",
        ),
        (
            _update("p", {"sessionUpdate": "session_message", "messageId": "x", "senderSessionId": "c"}),
            "senderSessionId",
        ),
    ],
)
def test_child_traffic_before_its_announcement_is_a_problem(message, mentions):
    children, problems = child_session_traffic(_traffic(message, _ANNOUNCE), {"p"})
    assert children == {"c"}
    assert len(problems) >= 1 and mentions in problems[0], problems


def test_an_announcement_on_an_unknown_session_does_not_announce():
    """The announcing update must itself be sent on a known session."""
    transcript = _traffic(_update("stranger", {"sessionUpdate": "subagent_update", "sessionId": "c"}), _CHILD_CHUNK)
    children, problems = child_session_traffic(transcript, {"p"})
    assert children == {"stranger", "c"}
    assert len(problems) == 2


def test_child_traffic_judgement_ignores_client_lines_and_responses():
    sent = TranscriptEntry.build(Direction.SENT, json.dumps({"jsonrpc": "2.0", **_CHILD_CHUNK}).encode(), 0.0)
    reply = _entry(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"sessionId": "other"}}))
    assert child_session_traffic([sent, reply], {"p"}) == (set(), [])


def _tool_update(session_id: str, kind: str = "tool_call_update", **fields: Any) -> dict[str, Any]:
    return _update(session_id, {"sessionUpdate": kind, "toolCallId": "t", **fields})


def _ref(session_id: str) -> dict[str, Any]:
    return {"type": "session", "sessionId": session_id}


def _permission(session_id: str, content: Any, subject_type: str = "tool_call") -> dict[str, Any]:
    """A v2 `session/request_permission` whose `tool_call` subject carries `content` (v2 has no
    top-level `toolCall`: it sits at `params.subject.toolCall`)."""
    subject: dict[str, Any] = {"type": subject_type}
    if subject_type == "tool_call":
        subject["toolCall"] = {"toolCallId": "t", "content": content}
    return {
        "id": 5,
        "method": "session/request_permission",
        "params": {"sessionId": session_id, "title": "ok?", "subject": subject, "options": []},
    }


def test_session_references_without_any_are_not_a_session_content_connection():
    transcript = _traffic(_tool_update("p", content=[{"type": "content", "content": {"type": "text", "text": "x"}}]))
    assert session_content_references(transcript, {"p"}) == ([], [])


def test_session_reference_to_a_known_session_is_conforming():
    transcript = _traffic(
        _tool_update("p", "tool_call", content=[_ref("p")]),  # a client-created session
        _ANNOUNCE,
        _tool_update("p", content=[_ref("c")]),
        _tool_update("p", "tool_call_content_chunk", content=_ref("c")),
        _permission("p", [_ref("c")]),
        # a nested child, announced on a known child, then referenced
        _update("c", {"sessionUpdate": "subagent_update", "sessionId": "g"}),
        _tool_update("c", content=[_ref("g")]),
    )
    assert session_content_references(transcript, {"p"}) == (["p", "c", "c", "c", "g"], [])


@pytest.mark.parametrize(
    ("message", "mentions"),
    [
        (_tool_update("p", content=[_ref("c")]), "tool_call_update"),
        (_tool_update("p", "tool_call", content=[_ref("c")]), "tool_call"),
        (_tool_update("p", "tool_call_content_chunk", content=_ref("c")), "tool_call_content_chunk"),
        (_permission("p", [_ref("c")]), "session/request_permission subject.toolCall"),
    ],
)
def test_session_reference_before_its_announcement_is_a_problem(message, mentions):
    references, problems = session_content_references(_traffic(message, _ANNOUNCE), {"p"})
    assert references == ["c"]
    assert len(problems) == 1 and mentions in problems[0] and "'c'" in problems[0], problems


def test_session_reference_in_the_announcing_message_itself_is_not_yet_known():
    """The announcement counts only for messages after it."""
    transcript = _traffic(
        _update("p", {"sessionUpdate": "subagent_update", "sessionId": "c", "content": [_ref("c")]}),
        _tool_update("p", content=[_ref("c")]),
    )
    assert session_content_references(transcript, {"p"}) == (["c"], [])


def test_session_reference_after_an_announcement_on_an_unknown_session_is_a_problem():
    transcript = _traffic(
        _update("stranger", {"sessionUpdate": "subagent_update", "sessionId": "c"}),
        _tool_update("p", content=[_ref("c")]),
    )
    references, problems = session_content_references(transcript, {"p"})
    assert references == ["c"] and len(problems) == 1


def test_session_reference_is_not_child_traffic():
    """An unknown reference alone is judged by `session_content_references`, not by
    `child_session_traffic` (so `ACP-SUBAGENT-001` is not double-counted)."""
    transcript = _traffic(_tool_update("p", content=[_ref("ghost")]))
    assert child_session_traffic(transcript, {"p"}) == (set(), [])
    assert len(session_content_references(transcript, {"p"})[1]) == 1


def test_session_reference_judgement_ignores_other_content_and_malformed_items():
    transcript = _traffic(
        _tool_update("p", content=["not a dict", {"type": "session"}, {"type": "session", "sessionId": 7}, {"type": "diff"}]),
        _tool_update("p", content="not a list"),
        {"id": 5, "method": "session/request_permission", "params": {"sessionId": "p", "subject": {"type": "tool_call", "toolCall": "nope"}}},
        _permission("p", "not a list"),
        # a command subject has no tool call, and the v1 top-level `toolCall` is not v2's carrier
        _permission("p", [_ref("ghost")], subject_type="command"),
        {"id": 6, "method": "session/request_permission", "params": {"sessionId": "p", "toolCall": {"toolCallId": "t", "content": [_ref("ghost")]}}},
        {"id": 7, "method": "session/request_permission", "params": {"sessionId": "p", "subject": None}},
    )
    assert session_content_references(transcript, {"p"}) == ([], [])


def _sub(outer: str, child: str, **fields: Any) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "subagent_update", "sessionId": child, **fields})


def test_no_subagent_update_is_not_a_subagent_connection():
    found = subagent_updates(_traffic(_update("p", {"sessionUpdate": "agent_message_chunk", "messageId": "m"})), {"p"})
    assert found == subagent_updates([], {"p"}) and found.updates == []
    assert not found.reported_directories


def test_a_stable_tree_with_absolute_directories_is_conforming():
    transcript = _traffic(
        _sub("p", "c", cwd="/work/c", additionalDirectories=["/work/x", "C:\\work", "\\\\srv\\share\\d"]),
        _sub("p", "c", title="again", cwd=None, additionalDirectories=[]),  # patch under the same parent
        _sub("c", "g"),  # nested child
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
    """A value of the wrong type is a schema defect (`ACP-PROMPT-002`'s): neither a relative path
    nor a reported directory, so `ACP-SUBAGENT-006` neither FAILs nor judges it."""
    found = subagent_updates(_traffic(_sub("p", "c", **fields)), {"p"})
    assert found.relative_paths == [] and not found.reported_directories


def test_is_absolute_path_accepts_native_absolute_syntaxes_only():
    assert all(is_absolute_path(path) for path in ("/a", "/", "C:\\a", "C:/a", "\\\\srv\\share"))
    assert not any(is_absolute_path(path) for path in ("a", "./a", "", "C:a", "\\a", "file:///a", None, 5))


def _msg(outer: str, message_id: str, **fields: Any) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "session_message", "messageId": message_id, **fields})


def _problems(found) -> tuple[int, int, int]:
    return len(found.same_participants), len(found.foreign_outer), len(found.unlinked_views)


def test_no_session_message_is_not_a_session_message_connection():
    found = session_messages(_traffic(_update("p", {"sessionUpdate": "session_message_chunk", "messageId": "m"})), {"p"})
    assert found.count == 0 and _problems(found) == (0, 0, 0)


def test_consistent_views_in_both_directions_are_conforming():
    transcript = _traffic(
        _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in"),
        _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="out"),
        # the child answers: outgoing on the child, incoming on the parent
        _msg("c", "ans-out", senderSessionId="c", recipientSessionId="p", recipientMessageId="ans-in"),
        _msg("p", "ans-in", senderSessionId="c", recipientSessionId="p", senderMessageId="ans-out"),
        _msg("p", "one-sided", recipientSessionId="c"),  # one participant: nothing to compare
    )
    found = session_messages(transcript, {"p"})
    assert found.count == 5 and _problems(found) == (0, 0, 0)


def test_equal_participants_are_judged_only_as_same_participants():
    for outer in ("p", "c"):  # whichever session the update is sent on
        found = session_messages(_traffic(_msg(outer, "m", senderSessionId="p", recipientSessionId="p")), {"p"})
        assert _problems(found) == (1, 0, 0), outer


def test_an_outer_session_that_is_neither_participant_is_judged_only_as_foreign_outer():
    found = session_messages(_traffic(_msg("g", "m", senderSessionId="p", recipientSessionId="c")), {"p"})
    assert _problems(found) == (0, 1, 0)
    # one known participant is not enough to judge the outer session
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


def test_a_repeated_defective_message_is_reported_once():
    transcript = _traffic(
        _msg("g", "m", senderSessionId="p", recipientSessionId="c"),
        _msg("g", "m", content=[]),
    )
    assert _problems(session_messages(transcript, {"p"})) == (0, 1, 0)


def test_conflicting_view_references_are_judged_only_as_unlinked_views():
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    for incoming in (
        _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="elsewhere"),
        _msg("c", "in", recipientSessionId="c", senderMessageId="elsewhere"),  # sender not repeated
    ):
        found = session_messages(_traffic(out, incoming), {"p"})
        assert _problems(found) == (0, 0, 1), found.unlinked_views
    # the reference arrives later with a metadata-only upsert, and is judged then
    late = session_messages(
        _traffic(
            out,
            _msg("c", "in", senderSessionId="p", recipientSessionId="c"),
            _msg("c", "in", senderMessageId="elsewhere"),
        ),
        {"p"},
    )
    assert _problems(late) == (0, 0, 1)
    # and a corrected reference clears it
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
    # the referenced view was never reported, or carries no reference back: nothing to compare
    assert _problems(session_messages(_traffic(out), {"p"})) == (0, 0, 0)
    bare = _msg("c", "in", senderSessionId="p", recipientSessionId="c")
    assert _problems(session_messages(_traffic(out, bare), {"p"})) == (0, 0, 0)
    # equal message IDs on two transcripts do not link them
    twin = _msg("c", "out", senderSessionId="p", recipientSessionId="c")
    assert _problems(session_messages(_traffic(out, twin), {"p"})) == (0, 0, 0)


def test_a_referenced_view_whose_sender_is_a_third_session_conflicts():
    """Both views carry references and they do not name each other, so it is judged even though
    the referenced view's own sender is neither of this message's participants."""
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    stranger = _msg("c", "in", senderSessionId="x", recipientSessionId="c", senderMessageId="elsewhere")
    found = session_messages(_traffic(out, stranger), {"p"})
    assert _problems(found) == (0, 0, 1) and found.links_judged == 1


def test_session_message_rows_count_only_what_they_judged():
    """The counts that decide a SKIP: `participants_judged` (007/008) is messages with both
    participants known, `links_judged` (009) view pairs that both carry a reference."""
    none = session_messages(_traffic(_msg("p", "m", content=[])), {"p"})
    assert (none.count, none.participants_judged, none.links_judged) == (1, 0, 0)
    one_sided = session_messages(_traffic(_msg("p", "m", senderSessionId="p", recipientMessageId="x")), {"p"})
    assert (one_sided.count, one_sided.participants_judged, one_sided.links_judged) == (1, 0, 0)
    out = _msg("p", "out", senderSessionId="p", recipientSessionId="c")
    bare_in = _msg("c", "in", senderSessionId="p", recipientSessionId="c")
    assert session_messages(_traffic(out, bare_in), {"p"}).participants_judged == 2  # not 009's
    assert session_messages(_traffic(out, bare_in), {"p"}).links_judged == 0
    # one outgoing view naming an unreported view, or one that has no reference back: not judged
    named = _msg("p", "out", senderSessionId="p", recipientSessionId="c", recipientMessageId="in")
    assert session_messages(_traffic(named), {"p"}).links_judged == 0
    assert session_messages(_traffic(named, bare_in), {"p"}).links_judged == 0
    linked = _msg("c", "in", senderSessionId="p", recipientSessionId="c", senderMessageId="out")
    both = session_messages(_traffic(named, linked), {"p"})
    assert both.links_judged == 2 and both.participants_judged == 2 and _problems(both) == (0, 0, 0)
    # repeated upserts of one message count it once
    twice = session_messages(_traffic(out, _msg("p", "out", content=[])), {"p"})
    assert twice.count == 2 and twice.participants_judged == 1


def _state(outer: str, state: str) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "state_update", "state": state})


def _mirror(state: str, parent: str = "p", child: str = "c") -> dict[str, Any]:
    return _update(
        parent, {"sessionUpdate": "subagent_update", "sessionId": child, "state": {"state": state}}
    )


def test_child_states_mirrored_in_either_order_are_conforming():
    transcript = _traffic(
        _ANNOUNCE,
        _state("c", "running"),
        _mirror("running"),
        _mirror("idle"),  # the mirror may precede the copy on the child's own stream
        _state("c", "idle"),
        _state("c", "idle"),  # a repeated snapshot needs no second mirror
        _state("p", "running"),  # the parent's own state is not a child's
    )
    found = child_state_mirrors(transcript, {"p"})
    assert (found.judged, found.unmirrored) == (2, [])


def test_a_child_state_with_no_mirror_is_reported():
    transcript = _traffic(_ANNOUNCE, _state("c", "running"), _mirror("running"), _state("c", "idle"))
    found = child_state_mirrors(transcript, {"p"})
    assert found.judged == 2 and len(found.unmirrored) == 1 and "'idle'" in found.unmirrored[0]
    # nothing mirrored at all, and a mirror on a session that is not the child's parent
    assert len(child_state_mirrors(_traffic(_ANNOUNCE, _state("c", "idle")), {"p"}).unmirrored) == 1
    elsewhere = _traffic(_ANNOUNCE, _state("c", "idle"), _mirror("idle", parent="g"))
    assert len(child_state_mirrors(elsewhere, {"p"}).unmirrored) == 1


def test_mirrors_must_follow_the_order_of_the_child_states():
    transcript = _traffic(
        _ANNOUNCE, _state("c", "running"), _state("c", "idle"), _mirror("idle"), _mirror("running")
    )
    assert len(child_state_mirrors(transcript, {"p"}).unmirrored) == 1


def test_an_unannounced_child_state_is_not_judged_for_mirroring():
    found = child_state_mirrors(_traffic(_state("c", "idle")), {"p"})
    assert (found.judged, found.unmirrored) == (0, [])


def _session_message(outer: str, message_id: str, **fields: Any) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "session_message", "messageId": message_id, **fields})


_TASK = _session_message("c", "in", senderSessionId="p", recipientSessionId="c")
_USER = _update("c", {"sessionUpdate": "user_message", "messageId": "u"})


def test_a_task_session_message_before_the_output_is_conforming():
    found = child_task_reports(_traffic(_ANNOUNCE, _TASK, _CHILD_CHUNK), {"p"})
    assert (found.started, found.judged, found.user_message_tasks, found.unreported) == (1, 1, [], [])
    # the sender may be supplied by a later upsert, before the output
    split = child_task_reports(
        _traffic(
            _ANNOUNCE,
            _session_message("c", "in", recipientSessionId="c"),
            _session_message("c", "in", senderSessionId="p"),
            _CHILD_CHUNK,
        ),
        {"p"},
    )
    assert split.unreported == []


def test_a_task_that_follows_or_misses_the_output_is_unreported():
    after = child_task_reports(_traffic(_ANNOUNCE, _CHILD_CHUNK, _TASK), {"p"})
    assert (after.started, len(after.unreported), after.user_message_tasks) == (1, 1, [])
    not_the_parent = _session_message("c", "in", senderSessionId="g", recipientSessionId="c")
    assert len(child_task_reports(_traffic(_ANNOUNCE, not_the_parent, _CHILD_CHUNK), {"p"}).unreported) == 1
    assert len(child_task_reports(_traffic(_ANNOUNCE, _CHILD_CHUNK), {"p"}).unreported) == 1


def test_a_user_message_task_is_judged_only_as_a_user_message():
    for user in (_USER, _update("c", {"sessionUpdate": "user_message_chunk", "messageId": "u"})):
        found = child_task_reports(_traffic(_ANNOUNCE, user, _CHILD_CHUNK), {"p"})
        assert (len(found.user_message_tasks), found.unreported) == (1, [])
        # `ACP-SUBAGENT-012` has nothing to judge here: the child still started, but it is 011's
        assert (found.started, found.judged) == (1, 0)
    # another child that was told its task properly is still judged
    mixed = child_task_reports(
        _traffic(
            _ANNOUNCE,
            _USER,
            _CHILD_CHUNK,
            _update("p", {"sessionUpdate": "subagent_update", "sessionId": "d"}),
            _session_message("d", "in", senderSessionId="p", recipientSessionId="d"),
            _update("d", {"sessionUpdate": "agent_message_chunk", "messageId": "m"}),
        ),
        {"p"},
    )
    assert (mixed.started, mixed.judged, mixed.unreported) == (2, 1, [])
    # a user message after the child's output is not the task that started it
    late = child_task_reports(_traffic(_ANNOUNCE, _TASK, _CHILD_CHUNK, _USER), {"p"})
    assert (late.user_message_tasks, late.unreported) == ([], [])
    # a child that never produces output is not judged for an unreported task
    quiet = child_task_reports(_traffic(_ANNOUNCE), {"p"})
    assert (quiet.started, quiet.unreported) == (0, [])


def test_task_traffic_of_an_unannounced_session_is_not_judged():
    found = child_task_reports(_traffic(_USER, _CHILD_CHUNK), {"p"})
    assert (found.started, found.user_message_tasks, found.unreported) == (0, [], [])


def _chunk(outer: str, message_id: str) -> dict[str, Any]:
    return _update(
        outer, {"sessionUpdate": "session_message_chunk", "messageId": message_id, "content": {}}
    )


def test_participants_before_the_first_chunk_are_conforming():
    transcript = _traffic(
        _session_message("p", "m", senderSessionId="p"),  # one participant is enough
        _chunk("p", "m"),
        _chunk("p", "m"),
        _session_message("p", "m", recipientSessionId="c"),
        _chunk("p", "never-named"),  # no participant is ever supplied: nothing to flag
    )
    found = session_message_streams(transcript, {"p"})
    assert (found.streamed, found.late_participants) == (2, [])


def test_participants_supplied_only_after_the_first_chunk_are_flagged():
    first_chunk = _traffic(_chunk("p", "m"), _session_message("p", "m", senderSessionId="p"))
    found = session_message_streams(first_chunk, {"p"})
    assert found.streamed == 1 and len(found.late_participants) == 1
    bare_upsert = _traffic(
        _session_message("p", "m", content=[]), _chunk("p", "m"), _session_message("p", "m", senderSessionId="p")
    )
    assert len(session_message_streams(bare_upsert, {"p"}).late_participants) == 1
    # null clears participants, so none is stored at the chunk
    cleared = _traffic(
        _session_message("p", "m", senderSessionId="p"),
        _session_message("p", "m", senderSessionId=None),
        _chunk("p", "m"),
        _session_message("p", "m", senderSessionId="p"),
    )
    assert len(session_message_streams(cleared, {"p"}).late_participants) == 1
    # a message on another transcript is another message
    other = _traffic(_session_message("c", "m", senderSessionId="p"), _chunk("p", "m"))
    assert session_message_streams(other, {"p"}).late_participants == []


def _config(outer: str, *options: dict[str, Any]) -> dict[str, Any]:
    return _update(outer, {"sessionUpdate": "config_option_update", "configOptions": list(options)})


def _select(current: str, *values: str, group: bool = False) -> dict[str, Any]:
    entries = [{"value": value, "name": value} for value in values]
    if group:
        entries = [{"groupId": "g", "name": "G", "options": entries}]
    return {"configId": "x", "name": "X", "type": "select", "currentValue": current, "options": entries}


def test_a_child_select_with_only_its_current_value_is_conforming():
    transcript = _traffic(
        _ANNOUNCE,
        _config("c", _select("a", "a"), {"configId": "b", "name": "B", "type": "boolean", "currentValue": True}),
        _config("c", _select("a", "a", group=True)),
    )
    found = child_config_selects(transcript, {"p"})
    assert (found.selects, found.with_choices) == (2, [])


def test_a_child_select_with_other_values_is_flagged():
    for option in (_select("a", "a", "b"), _select("a", "a", "b", group=True), _select("a", "b")):
        found = child_config_selects(_traffic(_ANNOUNCE, _config("c", option)), {"p"})
        assert found.selects == 1 and len(found.with_choices) == 1, option


def test_selects_of_the_clients_own_or_an_unannounced_session_are_not_judged():
    transcript = _traffic(_config("p", _select("a", "a", "b")), _config("c", _select("a", "a", "b")))
    assert child_config_selects(transcript, {"p"}).selects == 0
