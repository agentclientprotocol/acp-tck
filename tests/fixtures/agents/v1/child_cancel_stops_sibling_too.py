#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that `session/cancel` for one child
also stops the cancelled child's sibling (the per-child capability does not prevent the Agent from
cancelling its own delegated work, RFD:1071-1073, and that cannot be told from a leaked cancel).
The cancelled child confirms and the parent is left running, so `ACP-SUBAGENT-016` and `-017`
PASS, and the sibling's `idle`/`cancelled` is only recorded (`acp_tck_cancelled_siblings`). Within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildCancelStopsSiblingTooAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        for running in list(self._running_children.get(parent, [])):
            self._stop_child(parent, running)


def main() -> None:
    ChildCancelStopsSiblingTooAgent(agent_name="tck-fixture-child-cancel-stops-sibling-too").run()


if __name__ == "__main__":
    main()
