#!/usr/bin/env python3
"""Non-conforming fixture: `fork_copies_background_work.py`, except the forked session's turn
never ends (no idle). The fork's `running` snapshot still lists the source session's background
item, which a fork must not inherit (session-setup.mdx:49): `ACP-FORK-206` judges the snapshots it
received before the turn timed out and FAILs, next to `ACP-FORK-202` (the fork's turn never
ends). Within the `-k fork` scope.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkCopiesBackgroundWorkAndHangsAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._forks: set[Any] = set()

    def _fork_background(self, source_id: Any, session_id: Any) -> None:
        self._forks.add(session_id)
        self._background[session_id] = [dict(item) for item in self._background.get(source_id, [])]

    def _finish_turn(self, session_id: Any, stop_reason: str | None = None) -> None:
        if session_id not in self._forks:
            super()._finish_turn(session_id, stop_reason)


def main() -> None:
    ForkCopiesBackgroundWorkAndHangsAgent(
        capabilities={"session": {"fork": {}}},
        report_background_work=True,
        background_outlives_turn="keep",
    ).run()


if __name__ == "__main__":
    main()
