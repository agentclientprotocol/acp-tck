#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that on `session/cancel` for a child it can
no longer observe the child and reports `unknown` on the parent's `subagent_update.state` instead
of a confirmation. The cancellation is not observable: `ACP-SUBAGENT-016` SKIPs, `-017` (the parent
is left alone) PASSes. Within the `-k` scope of the `test_subagent_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildStateUnknownAfterCancelAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        self._report_child_state(parent, child_id, {"state": "unknown"})


def main() -> None:
    ChildStateUnknownAfterCancelAgent(agent_name="tck-fixture-child-state-unknown-after-cancel").run()


if __name__ == "__main__":
    main()
