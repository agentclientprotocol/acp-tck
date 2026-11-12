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
    _LIST_ROUTE_MAX_PAGES,
    PatchTracker,
    _route_from_list,
    agent_requests,
    assert_unknown_session_error,
    child_session_traffic,
    is_agent_initiated,
    is_response_line,
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
