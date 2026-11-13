#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that cancelling the parent ends its own
turn but leaves the foreground child it was waiting on running (RFD:1075-1087): the child keeps
reporting `running` and the parent lists no background work. FAILs exactly `ACP-SUBAGENT-202`.
Within the `-k` scope of the `test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ParentCancelLeavesChildRunningAgent(CancellableSubagentAgent):
    def _cascade_cancel(self, session_id: Any) -> None:
        pass


def main() -> None:
    ParentCancelLeavesChildRunningAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
