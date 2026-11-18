#!/usr/bin/env python3
"""Non-conforming fixture: reuses one `cursorId` for every cursor it announces, so the second
`cursor_update` for it carries a different anchor than the first (a cursor never moves). It
otherwise behaves like a conforming cursor-announcing agent. Violates ACP-CURSOR-001 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class CursorAnchorMovesAgent(CursorsMixin, ConformingAgent):
    def _new_cursor_id(self, session_id: Any) -> str:
        return "cur-shared"


def main() -> None:
    CursorAnchorMovesAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-cursor-anchor-moves"
    ).run()


if __name__ == "__main__":
    main()
