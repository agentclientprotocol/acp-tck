#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that the cancellable child ignores
`session/cancel` and finishes its work on its own about 1.5 s later (`idle`, `stopReason:
"end_turn"`), well after the race window in which an already-ended child could excuse that
(RFD:1089-1095). FAILs exactly `ACP-SUBAGENT-016`; the parent and the sibling are untouched
(`ACP-SUBAGENT-017` PASSes). Within the `-k` scope of the `test_subagent_controls.py` module, with
`--cancel-prompt __hang__` and `--timeout 4` (so the 1.5 s is inside the wait but past the race
window), unlike `child_ends_before_cancel.py`, whose child ends at once and is SKIPped.
"""

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildIgnoresCancelThenEndsAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        time.sleep(1.5)
        self._stop_child(parent, child_id, "end_turn")


def main() -> None:
    ChildIgnoresCancelThenEndsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
