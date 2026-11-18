#!/usr/bin/env python3
"""Non-conforming fixture: every full `session/resume` replay delivers its cursors under fresh
`cursorId`s, so the same anchor gets a different id on each replay. It otherwise behaves like a
conforming cursor-announcing agent. Violates ACP-CURSOR-004 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class UnstableCursorIdsAgent(CursorsMixin, ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._replay_count = 0

    def _replay_history(self, session_id: Any) -> None:
        self._replay_count += 1
        for update in self._history.get(session_id, []):
            if self._is_cursor(update):
                update = dict(update, cursorId=f"{update['cursorId']}-replay{self._replay_count}")
            self._notify("session/update", {"sessionId": session_id, "update": update})


def main() -> None:
    UnstableCursorIdsAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-unstable-cursor-ids"
    ).run()


if __name__ == "__main__":
    main()
