#!/usr/bin/env python3
"""Conforming fixture: its tool call and terminal advertise `capabilities.cancel`, and the agent
finishes both 0.25 s later (a final status and an `exitStatus`, both clearing `capabilities`), a
pause during which the TCK's `tool_call/cancel` and `terminal/cancel` arrive unread. It answers
them `-32602`, as tool-calls.mdx:459,605 require for an item that is already final, after the final
updates, so the driver reads the final update before the response and the `-32602` is a race:
`ACP-TOOLCANCEL-*` and `ACP-TERMCANCEL-*` all SKIP and nothing FAILs. The deterministic version of
`completes_before_cancel.py`, whose updates are written in one burst, so the driver usually sees
the final update before it sends anything. Within the `-k` scope of the `test_item_controls.py`
module, with `--cancel-prompt __hang__`.
"""

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RacesCancelWithCompletionAgent(ConformingAgent):
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


def main() -> None:
    RacesCancelWithCompletionAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
