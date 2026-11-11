#!/usr/bin/env python3
"""Conforming fixture: reports background work like `reports_background_work.py`, but asks
permission for its listed background tool call (the `tool_call` subject names it) instead of
finishing it at once. The request belongs to background work, so foreground work is not
blocked and the session never reports `requires_action` (tool-calls.mdx:268;
prompt-lifecycle.mdx:174): `ACP-PATCH-209` SKIPs rather than FAILs. Once answered, the tool
call ends `completed` if approved, else `cancelled`, and a repeated idle snapshot removes it
from the list.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AsksPermissionForBackgroundWorkAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._perm_counter = 0
        self._background_permissions: dict[Any, tuple[Any, str]] = {}  # id -> (session, tool call)

    def _run_background_work(self, session_id: Any) -> None:
        self._tool_call_count += 1
        tool_call_id = f"tool-bg-{self._tool_call_count:04d}"
        self._announce_background_item(session_id, tool_call_id)
        self._background.setdefault(session_id, []).append({"type": "tool_call", "toolCallId": tool_call_id})
        self._send_running_update(session_id)
        self._perm_counter += 1
        perm_id = f"perm-bg-{self._perm_counter}"
        self._background_permissions[perm_id] = (session_id, tool_call_id)
        self._write(
            {
                "jsonrpc": "2.0",
                "id": perm_id,
                "method": "session/request_permission",
                "params": {
                    "sessionId": session_id,
                    "title": "Keep watching for changes?",
                    "subject": {"type": "tool_call", "toolCall": {"toolCallId": tool_call_id}},
                    "options": [
                        {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
                    ],
                },
            }
        )

    def _handle_response(self, message: dict[str, Any]) -> None:
        pending = self._background_permissions.pop(message.get("id"), None)
        if pending is None:
            return
        session_id, tool_call_id = pending
        result = message.get("result") or {}
        outcome = result.get("outcome") if isinstance(result.get("outcome"), dict) else {}
        approved = outcome.get("outcome") == "selected" and outcome.get("optionId") == "allow-once"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "completed" if approved else "cancelled",
            },
        )
        listed = self._background.get(session_id, [])
        if {"type": "tool_call", "toolCallId": tool_call_id} in listed:
            listed.remove({"type": "tool_call", "toolCallId": tool_call_id})
        self._send_idle_update(session_id, None)


def main() -> None:
    AsksPermissionForBackgroundWorkAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
