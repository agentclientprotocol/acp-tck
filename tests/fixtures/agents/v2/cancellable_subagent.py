#!/usr/bin/env python3
"""Conforming fixture: its `__hang__` turn announces two running children of the prompted session,
`<id>-child-a` (advertises `capabilities.cancel`) and `<id>-child-b` (advertises nothing, but has
a tool call and a terminal of its own that advertise `capabilities.cancel`), each reporting its
`running` state on its own session and mirrored on the parent. The parent's `state_update`s carry
an empty `background` list (re-sent once the children are announced), so both children are
foreground work.

- `session/cancel` for child A stops that child only: it reports `idle` with `stopReason:
  "cancelled"` on its own session and on the parent association (RFD:1069-1073, 1089-1093). A
  cancel for a child that is no longer running is ignored (a cancel racing with ended work does
  not rewrite its outcome).
- `session/cancel` for the parent also stops every child it is waiting on, before the parent's own
  `idle`/`cancelled` (RFD:1075-1087).
- `tool_call/cancel` / `terminal/cancel` with child B's `sessionId` are accepted and confirmed
  (tool-calls.mdx:457,603), and leave B running.

Must PASS `ACP-SUBAGENT-016/017/202`, `ACP-TOOLCANCEL-203` and `ACP-TERMCANCEL-203` under
`--cancel-prompt __hang__`; other prompts expose no child. The `_`-hooks below are the seams the
violator fixtures override.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CancellableSubagentAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(report_background_work=True, cancellable_work=True, **kwargs)
        self._parent_of: dict[str, Any] = {}  # child sessionId -> parent sessionId
        self._running_children: dict[Any, list[str]] = {}  # parent -> children still running

    def _start_cancellable_work(self, session_id: Any) -> None:
        child_a, child_b = f"{session_id}-child-a", f"{session_id}-child-b"
        self._spawn_child(session_id, child_a, cancellable=True)
        self._spawn_child(session_id, child_b, cancellable=False)
        self._start_child_items(child_b)
        # The children are announced after the turn's first snapshot, so the agent re-sends the
        # state with its (still empty) `background` list (prompt-lifecycle.mdx:205): a client may
        # tell from it that they are foreground work.
        self._send_update(session_id, {"sessionUpdate": "state_update", "state": "running"})

    def _spawn_child(self, session_id: Any, child_id: str, *, cancellable: bool) -> None:
        update: dict[str, Any] = {
            "sessionUpdate": "subagent_update",
            "sessionId": child_id,
            "title": "helper",
        }
        if cancellable:
            update["capabilities"] = {"cancel": {}}
        self._send_update(session_id, update)
        self._parent_of[child_id] = session_id
        self._running_children.setdefault(session_id, []).append(child_id)
        self._send_child_state(session_id, child_id, {"state": "running"})

    def _send_child_state(self, session_id: Any, child_id: str, state: dict[str, Any]) -> None:
        """The child's own `state_update`, then its mirror on the parent association."""
        self._send_update(child_id, {"sessionUpdate": "state_update", **state})
        self._send_update(
            session_id, {"sessionUpdate": "subagent_update", "sessionId": child_id, "state": state}
        )

    def _start_child_items(self, child_id: str) -> None:
        """A tool call and a terminal of the child that advertise `cancel`, still live."""
        self._tool_call_count += 1
        self._terminal_count += 1
        tool_call_id = f"tool-child-{self._tool_call_count:04d}"
        terminal_id = f"term-child-{self._terminal_count:04d}"
        self._send_update(
            child_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Child waits on a long task",
                "kind": "execute",
                "status": "in_progress",
                "capabilities": {"cancel": {}},
            },
        )
        self._send_update(
            child_id,
            {
                "sessionUpdate": "terminal_update",
                "terminalId": terminal_id,
                "command": "sleep 600",
                "cwd": "/tmp",
                "capabilities": {"cancel": {}},
            },
        )
        self._open_tool_calls.setdefault(child_id, []).append(tool_call_id)
        self._open_terminals.setdefault(child_id, []).append(terminal_id)

    def _handle_cancel(self, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        parent = self._parent_of.get(session_id) if isinstance(session_id, str) else None
        if parent is None:
            super()._handle_cancel(params)
        elif session_id in self._running_children.get(parent, []):
            self._cancel_child(parent, session_id)

    def _cancel_child(self, parent: Any, child_id: str) -> None:
        """Hook: what `session/cancel` for a running child does. It stops that child only."""
        self._stop_child(parent, child_id)

    def _stop_child(self, parent: Any, child_id: str, stop_reason: str = "cancelled") -> None:
        for tool_call_id in list(self._open_tool_calls.get(child_id, [])):
            self._close_tool_call(child_id, tool_call_id)
        for terminal_id in list(self._open_terminals.get(child_id, [])):
            self._close_terminal(child_id, terminal_id)
        self._running_children[parent].remove(child_id)
        self._send_child_state(parent, child_id, {"state": "idle", "stopReason": stop_reason})

    def _finish_turn(self, session_id: Any, stop_reason: str | None = None) -> None:
        if stop_reason == "cancelled":
            self._cascade_cancel(session_id)
        super()._finish_turn(session_id, stop_reason)

    def _cascade_cancel(self, session_id: Any) -> None:
        """Hook: cancelling the parent also stops the children it is waiting on."""
        for child_id in list(self._running_children.get(session_id, [])):
            self._stop_child(session_id, child_id)


def main() -> None:
    CancellableSubagentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
