#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission (reporting `requires_action`), then on the answer
streams its reply and idles without reporting `running` first. Output after `requires_action`
is resumed progress, which MUST be reported as `running`: FAILs exactly `ACP-STATE-205`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class RequiresActionNoRunningAgent(AsksPermissionAgent):
    def _after_permission(self, session_id: Any, outcome: Any) -> None:
        self._finish_turn(session_id, "cancelled" if outcome == "cancelled" else "end_turn")


def main() -> None:
    RequiresActionNoRunningAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
