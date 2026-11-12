#!/usr/bin/env python3
"""Conforming fixture: its `__hang__` turn reports a tool call and a terminal that advertise
`capabilities.cancel` and then finish at once (a final status and an `exitStatus`, both clearing
`capabilities`), so nothing is cancellable by the time the client could act. `tool_call/cancel`
and `terminal/cancel` for them are answered `-32602`, as tool-calls.mdx:459,605 require for an
item that is already final. `ACP-TOOLCANCEL-201/202` and `ACP-TERMCANCEL-201/202` judge nothing
and SKIP; nothing FAILs. Within the `-k` scope of the `test_item_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CompletesBeforeCancelAgent(ConformingAgent):
    def _start_cancellable_work(self, session_id: Any) -> None:
        self._tool_call_count += 1
        self._terminal_count += 1
        tool_call_id = f"tool-quick-{self._tool_call_count:04d}"
        terminal_id = f"term-quick-{self._terminal_count:04d}"
        tool_call = {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id}
        terminal = {"sessionUpdate": "terminal_update", "terminalId": terminal_id}
        self._send_update(
            session_id,
            {**tool_call, "title": "A quick task", "status": "in_progress", "capabilities": {"cancel": {}}},
        )
        self._send_update(session_id, {**tool_call, "status": "completed", "capabilities": None})
        self._send_update(
            session_id, {**terminal, "command": "true", "cwd": "/tmp", "capabilities": {"cancel": {}}}
        )
        self._send_update(
            session_id, {**terminal, "exitStatus": {"exitCode": 0}, "capabilities": None}
        )


def main() -> None:
    CompletesBeforeCancelAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
