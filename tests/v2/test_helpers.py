"""Unit tests for the line classifiers and the `session/list` resume route in
`tck.v2.conformance._helpers`."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tck.common.harness import Direction, TranscriptEntry
from tck.v2.conformance._helpers import (
    _LIST_ROUTE_MAX_PAGES,
    _route_from_list,
    agent_requests,
    is_agent_initiated,
    is_response_line,
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
