#!/usr/bin/env python3
"""Conforming fixture: a `__hang__` turn starts a tool call and a terminal that advertise
`capabilities.cancel` and end at once, plus a live tool call and terminal that advertise no
`cancel`. When `tool_call/cancel` or `terminal/cancel` for one of the latter arrives, the item has
just become cancellable: the agent advertises `cancel` on it, accepts, and keeps cancelling it
until the turn ends. It answers a repeated request for that item `-32602` ("already being
cancelled", tool-calls.mdx:459,605) while the item stays live and advertised. Accepting also
starts a new cancellable tool call or terminal, which it cancels and confirms normally
(tool-calls.mdx:458,604).

The TCK sent one request per item, so its main request goes to the new item: `-201/202` PASS,
the not-cancellable rows (`-208/209`) SKIP for the race, the unknown-id rows (`-206/207`) PASS
and nothing FAILs. Within the `-k` scope of the `test_item_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsRepeatCancelWhileCancellingAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cancelling: dict[Any, list[tuple[str, str]]] = {}

    def _start_cancellable_work(self, session_id: Any) -> None:
        self._tool_call_count += 1
        tool_call_id = f"tool-quick-{self._tool_call_count:04d}"
        self._terminal_count += 1
        terminal_id = f"term-quick-{self._terminal_count:04d}"
        tool_call = {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id}
        terminal = {"sessionUpdate": "terminal_update", "terminalId": terminal_id}
        self._send_update(
            session_id,
            {**tool_call, "title": "Quick", "status": "in_progress", "capabilities": {"cancel": {}}},
        )
        self._send_update(session_id, {**tool_call, "status": "completed", "capabilities": None})
        self._send_update(session_id, {**terminal, "command": "true", "cwd": "/tmp", "capabilities": {"cancel": {}}})
        self._send_update(session_id, {**terminal, "exitStatus": {"exitCode": 0}, "capabilities": None})

    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not self._cancel_fixed(msg_id, params.get("sessionId"), str(params.get("toolCallId", ""))):
            super()._handle_tool_call_cancel(msg_id, params)

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not self._cancel_fixed(msg_id, params.get("sessionId"), str(params.get("terminalId", ""))):
            super()._handle_terminal_cancel(msg_id, params)

    def _cancel_fixed(self, msg_id: Any, session_id: Any, item_id: str) -> bool:
        """Answer a request for a fixed item; `False` for any other id."""
        cancelling = self._cancelling.setdefault(session_id, [])
        if any(item_id == cancelling_id for _kind, cancelling_id in cancelling):
            self._error(msg_id, -32602, "Already being cancelled")
            return True
        items = self._fixed_items.get(session_id, [])
        for kind, fixed_id in list(items):
            if fixed_id != item_id:
                continue
            items.remove((kind, fixed_id))
            cancelling.append((kind, item_id))
            self._send_update(session_id, {**self._update(kind, item_id), "capabilities": {"cancel": {}}})
            self._reply(msg_id, {})
            if kind == "tool_call":
                self._tool_call_count += 1
                new_id = f"tool-live-{self._tool_call_count:04d}"
                self._open_tool_calls.setdefault(session_id, []).append(new_id)
                update = {"title": "Waiting on a long task", "status": "in_progress"}
            else:
                self._terminal_count += 1
                new_id = f"term-live-{self._terminal_count:04d}"
                self._open_terminals.setdefault(session_id, []).append(new_id)
                update = {"command": "sleep 600", "cwd": "/tmp"}
            self._send_update(session_id, {**self._update(kind, new_id), **update, "capabilities": {"cancel": {}}})
            return True
        return False

    @staticmethod
    def _update(kind: str, item_id: str) -> dict[str, Any]:
        if kind == "tool_call":
            return {"sessionUpdate": "tool_call_update", "toolCallId": item_id}
        return {"sessionUpdate": "terminal_update", "terminalId": item_id}

    def _finish_cancellable_work(self, session_id: Any) -> None:
        super()._finish_cancellable_work(session_id)
        for kind, item_id in self._cancelling.pop(session_id, []):
            final = {"status": "cancelled"} if kind == "tool_call" else {"exitStatus": {"signal": "SIGTERM"}}
            self._send_update(session_id, {**self._update(kind, item_id), **final, "capabilities": None})


def main() -> None:
    RejectsRepeatCancelWhileCancellingAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
