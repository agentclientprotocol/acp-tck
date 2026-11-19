#!/usr/bin/env python3
"""Conforming fixture: advertises `session.fork` but never announces a cursor, and `session/fork`
rejects any `cursorId` with `-32602` since none was issued. ACP-CURSOR-003 probes it all the same
(literal reading of the rule) and PASSes; ACP-CURSOR-001, -002 and -004 SKIP.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class ForksWithoutCursorsAgent(CursorsMixin, ConformingAgent):
    def _send_user_message_update(self, session_id: Any, message_id: str, prompt: Any) -> None:
        ConformingAgent._send_user_message_update(self, session_id, message_id, prompt)


def main() -> None:
    ForksWithoutCursorsAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-forks-without-cursors"
    ).run()


if __name__ == "__main__":
    main()
