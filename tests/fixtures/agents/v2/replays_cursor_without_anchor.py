#!/usr/bin/env python3
"""Non-conforming fixture: announces cursors with their anchor live, but a full `session/resume`
replay delivers each cursor without its `anchor`. The first update the client sees for the rebuilt
cursor has no anchor (a replayed update carries the anchor, like a first update). It otherwise
behaves like a conforming cursor-announcing agent. Violates ACP-CURSOR-001 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class ReplaysCursorWithoutAnchorAgent(CursorsMixin, ConformingAgent):
    def _replay_history(self, session_id: Any) -> None:
        for update in self._history.get(session_id, []):
            if self._is_cursor(update):
                update = {key: value for key, value in update.items() if key != "anchor"}
            self._notify("session/update", {"sessionId": session_id, "update": update})


def main() -> None:
    ReplaysCursorWithoutAnchorAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-replays-cursor-without-anchor"
    ).run()


if __name__ == "__main__":
    main()
