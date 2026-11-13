#!/usr/bin/env python3
"""Conforming fixture: its tool call and terminal advertise `capabilities.cancel` while live.
When the request arrives it answers `-32602` ("already final") and only then sends the item's
final status or `exitStatus`, as an agent whose item ended internally before the notification was
flushed (tool-calls.mdx:459,605). The `-32602` comes with the final update, so it is not a
rejection: `ACP-TOOLCANCEL-*` and `ACP-TERMCANCEL-*` all SKIP and nothing FAILs. Within the `-k`
scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class FinalizesAfterRejectingCancelAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32602, "Tool call is already final")
        self._close_tool_call(params.get("sessionId"), str(params.get("toolCallId")))

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32602, "Terminal has already exited")
        self._close_terminal(params.get("sessionId"), str(params.get("terminalId")))


def main() -> None:
    FinalizesAfterRejectingCancelAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
