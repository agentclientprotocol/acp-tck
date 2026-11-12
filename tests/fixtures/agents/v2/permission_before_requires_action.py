#!/usr/bin/env python3
"""Conforming fixture: `asks_permission.py`, but it sends `session/request_permission` before
reporting `requires_action`, the order of the spec's own diagram (prompt-lifecycle.mdx:246-247).
`run_prompt`'s hold mode cancels while the session is still `running`, so `ACP-CANCEL-209`/
`ACP-CANCEL-213` are judged (and PASS) rather than SKIPped. FAILs nothing.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PermissionBeforeRequiresActionAgent(AsksPermissionAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        perm_id = self._next_permission_id()
        self._pending_permission = {"perm_id": perm_id, "session_id": session_id}
        self._send_permission_request(perm_id, session_id)
        self._send_update(session_id, {"sessionUpdate": "state_update", "state": "requires_action"})
        return True


def main() -> None:
    PermissionBeforeRequiresActionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
