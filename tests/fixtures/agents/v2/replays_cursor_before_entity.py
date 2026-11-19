#!/usr/bin/env python3
"""Non-conforming fixture: a full `session/resume` replay delivers every cursor before the entities
the cursors are anchored to (a replay delivers each entity before the cursors anchored to it). Live
cursors are fine. It otherwise behaves like a conforming cursor-announcing agent. Violates
ACP-CURSOR-002 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class ReplaysCursorBeforeEntityAgent(CursorsMixin, ConformingAgent):
    def _replay_history(self, session_id: Any) -> None:
        history = self._history.get(session_id, [])
        for update in [*(u for u in history if self._is_cursor(u)), *(u for u in history if not self._is_cursor(u))]:
            self._notify("session/update", {"sessionId": session_id, "update": update})


def main() -> None:
    ReplaysCursorBeforeEntityAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-replays-cursor-before-entity"
    ).run()


if __name__ == "__main__":
    main()
