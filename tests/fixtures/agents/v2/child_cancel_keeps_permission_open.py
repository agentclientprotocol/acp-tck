#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent_asks.py`, except a stopped child leaves its pending
permission request open instead of cancelling it with `$/cancel_request` (subagents.mdx:417). It
still confirms the cancellation. FAILs exactly `ACP-SUBAGENT-204` within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent_asks import CancellableSubagentAsksAgent  # noqa: E402


class ChildCancelKeepsPermissionOpenAgent(CancellableSubagentAsksAgent):
    def _withdraw_child_requests(self, child_id: str) -> None:
        pass


def main() -> None:
    ChildCancelKeepsPermissionOpenAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
