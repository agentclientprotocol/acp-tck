#!/usr/bin/env python3
"""Non-conforming fixture, Codex-style: each turn starts a command whose tool call references a
terminal and stays `in_progress`. The terminal is listed in `background` mid-turn, then exits
(`exitStatus`) and leaves the list, so the turn's idle lists nothing, yet the tool call is never
given a final status. A terminal that exited keeps nothing alive, so this is abandoned foreground
work that its tool call should have ended (tool-calls.mdx:423): FAILs exactly `ACP-PATCH-211`.
The negative control for the live-terminal condition of the exemption that
`references_background_terminal.py` exercises.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AbandonsToolCallAfterTerminalExitAgent(ConformingAgent):
    def _run_background_work(self, session_id: Any) -> None:
        self._terminal_count += 1
        self._tool_call_count += 1
        terminal_id = f"term-bg-{self._terminal_count:04d}"
        item = {"type": "terminal", "terminalId": terminal_id}
        self._send_update(
            session_id,
            {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "command": "make", "cwd": "/tmp"},
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": f"tool-cmd-{self._tool_call_count:04d}",
                "title": "Run the build",
                "kind": "execute",
                "status": "in_progress",
                "content": [{"type": "terminal", "terminalId": terminal_id}],
            },
        )
        listed = self._background.setdefault(session_id, [])
        listed.append(item)
        self._send_running_update(session_id)
        self._send_update(
            session_id,
            {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "exitStatus": {"exitCode": 0}},
        )
        listed.remove(item)
        self._send_running_update(session_id)


def main() -> None:
    AbandonsToolCallAfterTerminalExitAgent(
        capabilities={"session": {}}, report_background_work=True
    ).run()


if __name__ == "__main__":
    main()
