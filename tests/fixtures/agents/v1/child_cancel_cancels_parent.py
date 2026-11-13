#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that `session/cancel` for a child also
cancels its parent's turn (RFD:1069-1073: it cancels the child, not its parent). The child still
confirms its own cancellation, so `ACP-SUBAGENT-016` PASSes; the parent's prompt answered
`cancelled` FAILs exactly `ACP-SUBAGENT-017`. Within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildCancelCancelsParentAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        super()._cancel_child(parent, child_id)
        ConformingAgent._handle_notification(self, "session/cancel", {"sessionId": parent})


def main() -> None:
    ChildCancelCancelsParentAgent(agent_name="tck-fixture-child-cancel-cancels-parent").run()


if __name__ == "__main__":
    main()
