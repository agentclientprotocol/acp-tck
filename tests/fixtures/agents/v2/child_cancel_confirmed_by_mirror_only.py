#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that on `session/cancel` for a child the
`idle` with `stopReason: "cancelled"` is reported only as the mirror on the parent's
`subagent_update.state`, never as a `state_update` on the child's own session. The docs name the
child's own `state_update` as the confirmation (`subagents.mdx:400`) and make the mirror only a
SHOULD, so FAILs exactly `ACP-SUBAGENT-016`; the parent and the other child are untouched
(`ACP-SUBAGENT-017` PASSes). Within the `-k` scope of the `test_subagent_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildCancelConfirmedByMirrorOnlyAgent(CancellableSubagentAgent):
    _mirror_only = False

    def _cancel_child(self, parent: Any, child_id: str) -> None:
        self._mirror_only = True
        try:
            super()._cancel_child(parent, child_id)
        finally:
            self._mirror_only = False

    def _send_child_state(self, session_id: Any, child_id: str, state: dict[str, Any]) -> None:
        if not self._mirror_only:
            super()._send_child_state(session_id, child_id, state)
            return
        self._send_update(
            session_id, {"sessionUpdate": "subagent_update", "sessionId": child_id, "state": state}
        )


def main() -> None:
    ChildCancelConfirmedByMirrorOnlyAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
