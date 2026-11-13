#!/usr/bin/env python3
"""Non-conforming fixture: its tool call keeps advertising `capabilities.cancel` after it is final
(as `keeps_cancel_after_final.py`), and a further `tool_call/cancel` for it is rejected with
`-32603` instead of `-32602` (tool-calls.mdx:459). The rejection itself is right, so FAILs exactly
the ADVISORY `ACP-TOOLCANCEL-205`. Within the `-k` scope of the `test_item_controls.py` module,
with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class FinalToolCallCancelWrongCodeAgent(ConformingAgent):
    def _close_tool_call(self, session_id: Any, tool_call_id: str) -> None:
        self._open_tool_calls[session_id].remove(tool_call_id)
        self._send_update(
            session_id,
            {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id, "status": "cancelled"},
        )

    def _close_terminal(self, session_id: Any, terminal_id: str) -> None:
        self._open_terminals[session_id].remove(terminal_id)
        self._send_update(
            session_id,
            {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "exitStatus": {"signal": "SIGTERM"}},
        )

    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        item_id = str(params.get("toolCallId", ""))
        if item_id.startswith("tool-live-") and item_id not in self._open_tool_calls.get(params.get("sessionId"), []):
            self._error(msg_id, -32603, "Internal error")  # a final tool call that still advertises `cancel`
            return
        super()._handle_tool_call_cancel(msg_id, params)


def main() -> None:
    FinalToolCallCancelWrongCodeAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
