#!/usr/bin/env python3
"""Non-conforming fixture: its terminal keeps advertising `capabilities.cancel` after it reports
`exitStatus` (as `keeps_cancel_after_final.py`), and a further `terminal/cancel` for it is
answered with an empty result instead of an error. The agent responds with an error for an exited
terminal (tool-calls.mdx:605): FAILs exactly `ACP-TERMCANCEL-204` (`-205` SKIPs: nothing was
rejected). Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt
__hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsCancelForExitedTerminalAgent(ConformingAgent):
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

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        item_id = str(params.get("terminalId", ""))
        if item_id.startswith("term-live-") and item_id not in self._open_terminals.get(params.get("sessionId"), []):
            self._reply(msg_id, {})  # a final terminal that still advertises `cancel`
            return
        super()._handle_terminal_cancel(msg_id, params)


def main() -> None:
    AcceptsCancelForExitedTerminalAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
