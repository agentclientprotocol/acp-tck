#!/usr/bin/env python3
"""Non-conforming fixture: announces each cursor with a first `cursor_update` that has no `anchor`
(the first update for a `cursorId` MUST include it). It otherwise behaves like a conforming
cursor-announcing agent. Violates ACP-CURSOR-001 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"fork": {}}}


class CursorWithoutAnchorAgent(CursorsMixin, ConformingAgent):
    def _cursor_update(self, cursor_id: str, anchor: dict[str, Any]) -> dict[str, Any]:
        update = super()._cursor_update(cursor_id, anchor)
        del update["anchor"]
        return update


def main() -> None:
    CursorWithoutAnchorAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-cursor-no-anchor").run()


if __name__ == "__main__":
    main()
