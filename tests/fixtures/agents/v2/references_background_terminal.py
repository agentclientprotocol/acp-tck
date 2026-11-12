#!/usr/bin/env python3
"""Conforming fixture, Codex-style: each turn starts a command whose tool call references a
terminal (a `terminal` content item) and stays `in_progress` while the process runs. The
terminal is announced, listed in `background` and still running at the turn-ending idle; the
tool call itself is not listed. A tool call that references a listed terminal is live
(prompt-lifecycle.mdx:216,998,1175), so `ACP-PATCH-211` PASSes, as do `ACP-STATE-206..208`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ReferencesBackgroundTerminalAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._commands: dict[Any, list[tuple[str, str]]] = {}  # sessionId -> (terminalId, toolCallId)

    def _run_background_work(self, session_id: Any) -> None:
        self._terminal_count += 1
        self._tool_call_count += 1
        terminal_id = f"term-bg-{self._terminal_count:04d}"
        tool_call_id = f"tool-cmd-{self._tool_call_count:04d}"
        self._commands.setdefault(session_id, []).append((terminal_id, tool_call_id))
        self._announce_command(session_id, terminal_id, tool_call_id)
        self._background.setdefault(session_id, []).append({"type": "terminal", "terminalId": terminal_id})
        self._send_running_update(session_id)

    def _announce_command(self, session_id: Any, terminal_id: str, tool_call_id: str) -> None:
        self._send_update(
            session_id,
            {
                "sessionUpdate": "terminal_update",
                "terminalId": terminal_id,
                "command": "npm run dev",
                "cwd": "/tmp",
            },
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Run the dev server",
                "kind": "execute",
                "status": "in_progress",
                "content": [{"type": "terminal", "terminalId": terminal_id}],
            },
        )

    def _resume_background(self, session_id: Any) -> None:
        """The resume snapshot lists the running terminals, so each is announced again first
        (session-setup.mdx:346)."""
        for terminal_id, tool_call_id in self._commands.get(session_id, []):
            self._announce_command(session_id, terminal_id, tool_call_id)


def main() -> None:
    ReferencesBackgroundTerminalAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
