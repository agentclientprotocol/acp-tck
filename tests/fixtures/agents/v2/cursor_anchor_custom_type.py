#!/usr/bin/env python3
"""Non-conforming fixture: anchors each cursor with a `type` (`"hologram"`) that is neither defined
nor `_`-prefixed, and a `position` (`"beside"`) likewise. The `other` branches accept any string, so
schema validation does not cascade and ACP-CURSOR-001..004 ignore an anchor of unknown `type`.
Violates `ACP-ENUM-201` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402


class CursorAnchorCustomTypeAgent(CursorsMixin, ConformingAgent):
    def _anchor_for(self, message_id: str) -> dict[str, Any]:
        return {"type": "hologram", "messageId": message_id, "position": "beside"}


def main() -> None:
    CursorAnchorCustomTypeAgent(
        capabilities={"session": {"fork": {}}}, agent_name="tck-fixture-cursor-anchor-custom-type"
    ).run()


if __name__ == "__main__":
    main()
