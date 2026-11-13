#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that the cancellable child finishes on its
own (`idle`, `stopReason: "end_turn"`) just as `session/cancel` reaches the agent, so the cancel
finds no running work: a cancellation racing with already-ended work does not rewrite its outcome
(RFD:1093-1095). `ACP-SUBAGENT-016` and `-017` judge nothing and SKIP; nothing FAILs. Within the
`-k` scope of the `test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildEndsBeforeCancelAgent(CancellableSubagentAgent):
    def _cancel_child(self, parent: Any, child_id: str) -> None:
        self._stop_child(parent, child_id, "end_turn")


def main() -> None:
    ChildEndsBeforeCancelAgent(agent_name="tck-fixture-child-ends-before-cancel").run()


if __name__ == "__main__":
    main()
