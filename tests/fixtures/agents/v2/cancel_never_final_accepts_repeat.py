#!/usr/bin/env python3
"""Non-conforming fixture: `tool_call/cancel` and `terminal/cancel` for its advertised, running
items are answered with an empty result, and the agent stops advertising `cancel` at once
(`capabilities: null`), but the items get no final status or `exitStatus` until the turn ends.
The Agent confirms an accepted cancel with a final update (tool-calls.mdx:458,604): FAILs exactly
`ACP-TOOLCANCEL-202` and `ACP-TERMCANCEL-202`. A repeated request for an item it is already
cancelling is accepted again, but the TCK does not send one: the item it already cancelled is not
a not-cancellable target, so `-208/209` SKIP rather than repeat the `-202` defect. Within the
`-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CancelNeverFinalAcceptsRepeatAgent(ConformingAgent):
    # The base handlers answer `{}` for an item still open, the cancelled one included.
    def _confirm_tool_call_cancel(self, session_id: Any, tool_call_id: str) -> None:
        self._send_update(
            session_id, {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id, "capabilities": None}
        )

    def _confirm_terminal_cancel(self, session_id: Any, terminal_id: str) -> None:
        self._send_update(
            session_id, {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "capabilities": None}
        )


def main() -> None:
    CancelNeverFinalAcceptsRepeatAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
