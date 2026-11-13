#!/usr/bin/env python3
"""Conforming fixture: after each turn's idle it starts background work, a tool call that
advertises `capabilities.cancel` and is listed in `background`. `tool_call/cancel` for it is
accepted, but the agent asks the client's permission before it stops (tool-calls.mdx:268 allows a
request for background work at any time) and confirms with the final status only once the request
is answered. The TCK must answer agent requests it reads after the turn's idle:
`ACP-TOOLCANCEL-201/202` PASS (nothing FAILs). Within the `-k` scope of the `test_item_controls.py`
module, with the default prompt.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ConfirmsCancelAfterPermissionAnswerAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._work: dict[Any, tuple[Any, str]] = {}  # permission id -> (session, tool call)
        self._cancellable: dict[Any, str] = {}  # sessionId -> toolCallId, live

    def _run_background_work(self, session_id: Any) -> None:
        pass

    def _finish_turn(self, session_id: Any, stop_reason: str | None = None) -> None:
        super()._finish_turn(session_id, stop_reason)
        self._tool_call_count += 1
        tool_call_id = f"tool-bg-{self._tool_call_count:04d}"
        self._cancellable[session_id] = tool_call_id
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Watching for changes",
                "kind": "other",
                "status": "in_progress",
                "capabilities": {"cancel": {}},
            },
        )
        self._background.setdefault(session_id, []).append({"type": "tool_call", "toolCallId": tool_call_id})
        self._resend_background_state(session_id)

    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id, tool_call_id = params.get("sessionId"), str(params.get("toolCallId"))
        if self._cancellable.get(session_id) != tool_call_id:
            self._error(msg_id, -32602, "Unknown, final or not cancellable tool call")
            return
        self._reply(msg_id, {})
        perm_id = f"perm-bg-{tool_call_id}"
        self._work[perm_id] = (session_id, tool_call_id)
        self._write(
            {
                "jsonrpc": "2.0",
                "id": perm_id,
                "method": "session/request_permission",
                "params": {
                    "sessionId": session_id,
                    "title": "Stop watching?",
                    "subject": {"type": "tool_call", "toolCall": {"toolCallId": tool_call_id}},
                    "options": [
                        {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
                    ],
                },
            }
        )

    def _handle_response(self, message: dict[str, Any]) -> None:
        pending = self._work.pop(message.get("id"), None)
        if pending is None:
            return
        session_id, tool_call_id = pending
        del self._cancellable[session_id]
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "cancelled",
                "capabilities": None,
            },
        )
        self._background[session_id].remove({"type": "tool_call", "toolCallId": tool_call_id})
        self._resend_background_state(session_id)


def main() -> None:
    ConfirmsCancelAfterPermissionAnswerAgent(
        capabilities={"session": {}}, report_background_work=True, cancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
