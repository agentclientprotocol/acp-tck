#!/usr/bin/env python3
"""Non-conforming fixture: `session/fork` accepts any `cursorId`, forking the whole session when the
cursor was never issued (as if `cursorId` had been omitted). It otherwise behaves like a conforming
cursor-announcing agent. Violates ACP-CURSOR-003 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"fork": {}}}


class ForkIgnoresCursorIdAgent(CursorsMixin, ConformingAgent):
    def _cursor_rejected(self, session_id: Any, cursor_id: Any) -> bool:
        return False


def main() -> None:
    ForkIgnoresCursorIdAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-fork-ignores-cursor-id").run()


if __name__ == "__main__":
    main()
