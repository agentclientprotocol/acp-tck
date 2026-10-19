#!/usr/bin/env python3
"""Conforming fixture: foreground work starts blocked on a permission request, so the first
state it reports is `requires_action` (no preliminary `running`), then `running` once the
answer lets it resume, then `idle(end_turn)`. Must PASS `ACP-STATE-201/202/205` and
`ACP-PATCH-209`: `requires_action` is an active state in its own right.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class StartsBlockedAgent(AsksPermissionAgent):
    def _send_running_update(self, session_id: Any) -> None:
        pass  # the turn starts in `requires_action`, reported by `_mid_turn_action`


def main() -> None:
    StartsBlockedAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
