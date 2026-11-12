#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that `session/cancel` for one child
stops every running child of the parent, siblings included (RFD:1069-1073: it cancels the child,
not its siblings). The cancelled child confirms, so `ACP-SUBAGENT-016` PASSes; the sibling's
`idle`/`cancelled` FAILs exactly `ACP-SUBAGENT-017`. Within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildCancelCancelsSiblingAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        for running in list(self._running_children.get(parent, [])):
            self._stop_child(parent, running)


def main() -> None:
    ChildCancelCancelsSiblingAgent(agent_name="tck-fixture-child-cancel-cancels-sibling").run()


if __name__ == "__main__":
    main()
