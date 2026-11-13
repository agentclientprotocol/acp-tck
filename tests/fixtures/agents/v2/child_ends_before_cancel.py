#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that the cancellable child finishes on its
own (`idle`, `stopReason: "end_turn"`) just as the TCK's requests reach the agent, so the
`session/cancel` for it finds no running work and is ignored: a cancellation racing with
already-ended work does not rewrite its outcome (RFD:1093-1095). `ACP-SUBAGENT-016` and `-017`
judge nothing and SKIP; nothing FAILs. Cancelling the parent still stops the other child
(`ACP-SUBAGENT-202` PASSes). Within the `-k` scope of the `test_subagent_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildEndsBeforeCancelAgent(CancellableSubagentAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_tool_call_cancel(msg_id, params)
        for parent, running in self._running_children.items():
            for child_id in list(running):
                if child_id.endswith("-child-a"):
                    self._stop_child(parent, child_id, "end_turn")


def main() -> None:
    ChildEndsBeforeCancelAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
