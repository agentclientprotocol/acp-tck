#!/usr/bin/env python3
"""Non-conforming fixture: a terminal sends output after it reported `exitStatus`.

FAILs `ACP-PATCH-216` (ADVISORY: agents send all output before a concrete `exitStatus`). The chunk
is valid base64 for a known terminal, so nothing else FAILs.

`_send_rich_turn_updates` is overridden outright, so the other patch rows SKIP "no <variant>
observed".
"""

import base64
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class OutputAfterExitAgent(ConformingAgent):
    def _send_rich_turn_updates(self, session_id: Any) -> None:
        self._terminal_count += 1
        terminal_id = f"term-{self._terminal_count:04d}"
        self._send_update(
            session_id,
            {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "command": "echo hi", "cwd": "/tmp"},
        )
        self._send_update(
            session_id,
            {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "exitStatus": {"exitCode": 0}},
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "terminal_output_chunk",
                "terminalId": terminal_id,
                "data": base64.b64encode(b"hi\n").decode("ascii"),
            },
        )


def main() -> None:
    OutputAfterExitAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
