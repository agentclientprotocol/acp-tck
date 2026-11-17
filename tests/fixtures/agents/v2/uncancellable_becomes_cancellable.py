#!/usr/bin/env python3
"""Conforming fixture for the not-cancellable cancel rows: like `conforming_full.py`, a `__hang__`
turn starts a live tool call and terminal that advertise no `cancel`. When `tool_call/cancel` or
`terminal/cancel` for one of them arrives, the item has just become cancellable: the agent
advertises `capabilities.cancel` on it (for the tool call before its response, for the terminal
right after it), accepts the request and confirms the cancel, as an agent whose item gained the
control as the request crossed (tool-calls.mdx:440,458,604). The result is legitimate, so `ACP-TOOLCANCEL-208/209` and `ACP-TERMCANCEL-208/209` SKIP for the race
and nothing FAILs. Within the `-k` scope of the `test_item_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UncancellableBecomesCancellableAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id, tool_call_id = params.get("sessionId"), str(params.get("toolCallId", ""))
        if tool_call_id.startswith("tool-fixed-") and self._advertise_cancel(session_id, tool_call_id):
            self._open_tool_calls.setdefault(session_id, []).append(tool_call_id)
        super()._handle_tool_call_cancel(msg_id, params)  # `{}`, then `cancelled`

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id, terminal_id = params.get("sessionId"), str(params.get("terminalId", ""))
        if not terminal_id.startswith("term-fixed-"):
            super()._handle_terminal_cancel(msg_id, params)
            return
        self._reply(msg_id, {})
        time.sleep(0.15)  # the advertisement follows the response, inside the TCK's grace window
        if self._advertise_cancel(session_id, terminal_id):
            self._open_terminals.setdefault(session_id, []).append(terminal_id)
            self._close_terminal(session_id, terminal_id)

    def _advertise_cancel(self, session_id: Any, item_id: str) -> bool:
        """Move a live fixed item to the cancellable ones, advertising `cancel` on it."""
        items = self._fixed_items.get(session_id, [])
        for kind, fixed_id in list(items):
            if fixed_id == item_id:
                items.remove((kind, fixed_id))
                if kind == "tool_call":
                    update = {"sessionUpdate": "tool_call_update", "toolCallId": item_id}
                else:
                    update = {"sessionUpdate": "terminal_update", "terminalId": item_id}
                self._send_update(session_id, {**update, "capabilities": {"cancel": {}}})
                return True
        return False


def main() -> None:
    UncancellableBecomesCancellableAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
