#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that on `session/cancel` for a child it first
reports `unknown` (it lost sight of the child) and then, once it observes the work stopped,
confirms with `idle` and `stopReason: "cancelled"`. The later confirmation still decides
`ACP-SUBAGENT-016`, which PASSes, as does `-017`. Within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildUnknownThenCancelledAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        self._send_child_state(parent, child_id, {"state": "unknown"})
        self._stop_child(parent, child_id)


def main() -> None:
    ChildUnknownThenCancelledAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
