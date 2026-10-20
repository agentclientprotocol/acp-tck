#!/usr/bin/env python3
"""Conforming fixture: asks for permission (reporting `requires_action`), then whatever the
answer, ends the work without resuming: `requires_action` -> `idle(end_turn)`, no `running` and
no further output. The spec allows `idle` straight from `requires_action`, so this must PASS
`ACP-PATCH-209`/`ACP-STATE-201`/`ACP-STATE-205` (and `ACP-CANCEL-209` on a cancelled outcome).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class RequiresActionThenIdleAgent(AsksPermissionAgent):
    def _after_permission(self, session_id: Any, outcome: Any) -> None:
        self._send_idle_update(session_id, "cancelled" if outcome == "cancelled" else "end_turn")


def main() -> None:
    RequiresActionThenIdleAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
