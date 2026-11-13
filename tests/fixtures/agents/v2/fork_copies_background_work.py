#!/usr/bin/env python3
"""Non-conforming fixture: `keeps_background_work.py`, except a fork inherits the source session's
background list, so the fork's snapshots list work it never started. A fork starts with no
background work (session-setup.mdx:49).

FAILs exactly `ACP-FORK-206`. The inherited item was announced for the source session only, but
the background rows judge a fresh, unforked session, so `ACP-STATE-207` does not cascade.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkCopiesBackgroundWorkAgent(ConformingAgent):
    def _fork_background(self, source_id: Any, session_id: Any) -> None:
        self._background[session_id] = [dict(item) for item in self._background.get(source_id, [])]


def main() -> None:
    ForkCopiesBackgroundWorkAgent(
        capabilities={"session": {"fork": {}}},
        report_background_work=True,
        background_outlives_turn="keep",
    ).run()


if __name__ == "__main__":
    main()
