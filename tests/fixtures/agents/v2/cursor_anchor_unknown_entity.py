#!/usr/bin/env python3
"""Non-conforming fixture: anchors each cursor to a message id it never reported on the session. It
otherwise behaves like a conforming cursor-announcing agent. Violates ACP-CURSOR-002 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class CursorAnchorUnknownEntityAgent(CursorsMixin, ConformingAgent):
    def _anchor_for(self, message_id: str) -> dict[str, Any]:
        return super()._anchor_for(f"{message_id}-never-reported")


def main() -> None:
    CursorAnchorUnknownEntityAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-cursor-anchor-unknown-entity"
    ).run()


if __name__ == "__main__":
    main()
