#!/usr/bin/env python3
"""Fixture for `ACP-INFO-BACKGROUND-201`: `references_background_terminal.py`, except the
background list names the command's tool call as well as its terminal. Process-backed work is
listed as its terminal only (prompt-lifecycle.mdx:208), but the client cannot tell whether the
tool call has other live work, so the row only records the pair and nothing FAILs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from references_background_terminal import ReferencesBackgroundTerminalAgent  # noqa: E402


class ListsToolCallWithItsTerminalAgent(ReferencesBackgroundTerminalAgent):
    def _run_background_work(self, session_id: Any) -> None:
        super()._run_background_work(session_id)
        _terminal_id, tool_call_id = self._commands[session_id][-1]
        self._background[session_id].append({"type": "tool_call", "toolCallId": tool_call_id})
        self._send_running_update(session_id)


def main() -> None:
    ListsToolCallWithItsTerminalAgent(
        capabilities={"session": {}}, report_background_work=True
    ).run()


if __name__ == "__main__":
    main()
