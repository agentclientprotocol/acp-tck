#!/usr/bin/env python3
"""Non-conforming fixture: `asks_permission.py`, but it never reports `requires_action` while
its foreground work is blocked on the permission request (the session stays `running`).
Blocked foreground work SHOULD report `requires_action` (tool-calls.mdx:209): FAILs exactly
`ACP-PATCH-209`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PermissionWithoutRequiresActionAgent(AsksPermissionAgent):
    def _send_update(self, session_id: Any, update: dict[str, Any]) -> None:
        if update.get("sessionUpdate") == "state_update" and update.get("state") == "requires_action":
            return
        super()._send_update(session_id, update)


def main() -> None:
    PermissionWithoutRequiresActionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
