#!/usr/bin/env python3
"""Non-conforming fixture: its tool call and terminal advertise `capabilities.cancel` and finish
0.25 s later (like `races_cancel_with_completion.py`), but the agent implements neither
`tool_call/cancel` nor `terminal/cancel`: it answers both `-32601` after the final updates.
Only `-32602` is the documented answer for an item that is already final (tool-calls.mdx:459,605),
so the race excuse does not apply and the missing methods are not hidden: FAILs
`ACP-TOOLCANCEL-201` and `ACP-TERMCANCEL-201` (`-202` SKIP: nothing was accepted). Within the
`-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CancelMissingAfterCompletionAgent(ConformingAgent):
    def _start_cancellable_work(self, session_id: Any) -> None:
        self._tool_call_count += 1
        self._terminal_count += 1
        tool_call = {
            "sessionUpdate": "tool_call_update",
            "toolCallId": f"tool-quick-{self._tool_call_count:04d}",
        }
        terminal = {"sessionUpdate": "terminal_update", "terminalId": f"term-quick-{self._terminal_count:04d}"}
        self._send_update(
            session_id,
            {**tool_call, "title": "A quick task", "status": "in_progress", "capabilities": {"cancel": {}}},
        )
        self._send_update(
            session_id, {**terminal, "command": "true", "cwd": "/tmp", "capabilities": {"cancel": {}}}
        )
        time.sleep(0.25)
        self._send_update(session_id, {**tool_call, "status": "completed", "capabilities": None})
        self._send_update(session_id, {**terminal, "exitStatus": {"exitCode": 0}, "capabilities": None})

    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32601, "Method not found")

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32601, "Method not found")


def main() -> None:
    CancelMissingAfterCompletionAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
