#!/usr/bin/env python3
"""Conforming fixture for the already-final cancel rows: its tool call and terminal advertise
`capabilities.cancel`, and once `tool_call/cancel` / `terminal/cancel` is accepted and the item
is final (a final status, an `exitStatus`) it keeps advertising `cancel` (the patch omits
`capabilities`). It should have stopped (tool-calls.mdx:440,600, a SHOULD that
`ACP-PATCH-212` judges), so the client may still send a request, and the agent answers it
`-32602` as tool-calls.mdx:459,605 say: `ACP-TOOLCANCEL-201/202/204/205` and
`ACP-TERMCANCEL-201/202/204/205` all PASS. Within the `-k` scope of the `test_item_controls.py`
module, with `--cancel-prompt __hang__`. `ACP-PATCH-212` FAILs outside it.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class KeepsCancelAfterFinalAgent(ConformingAgent):
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
            {
                "sessionUpdate": "terminal_update",
                "terminalId": terminal_id,
                "exitStatus": {"signal": "SIGTERM"},
            },
        )


def main() -> None:
    KeepsCancelAfterFinalAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
