#!/usr/bin/env python3
"""Conforming fixture: `cancellable_subagent.py`, except that its children have no tool call or
terminal until the parent is cancelled: after stopping the children, the agent announces a tool
call and a terminal of the sibling child that advertise `capabilities.cancel`, right before the
parent's `idle`. They are the first cancellable items the TCK sees, so its `tool_call/cancel` and
`terminal/cancel` are still in flight when the cascade ends. The agent accepts and confirms them
(tool-calls.mdx:457-459,603-605): `ACP-TOOLCANCEL-203` and `ACP-TERMCANCEL-203` PASS and nothing
FAILs; a request still awaiting its answer at the end of the run must be judged, not reported as
raced. With `--cancel-prompt __hang__`, within the `-k` scope of the `test_subagent_controls.py`
module.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildItemsCancellableAtCascadeEndAgent(CancellableSubagentAgent):
    def _start_child_items(self, child_id: str) -> None:
        pass

    def _cascade_cancel(self, session_id: Any) -> None:
        super()._cascade_cancel(session_id)
        super()._start_child_items(f"{session_id}-child-b")


def main() -> None:
    ChildItemsCancellableAtCascadeEndAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
