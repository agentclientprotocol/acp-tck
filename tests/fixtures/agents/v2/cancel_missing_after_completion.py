#!/usr/bin/env python3
"""Non-conforming fixture: its tool call and terminal advertise `capabilities.cancel` and finish
once the requests arrive (like `races_cancel_with_completion.py`), but the agent implements neither
`tool_call/cancel` nor `terminal/cancel`: it answers both `-32601` after the final updates.
Only `-32602` is the documented answer for an item that is already final (tool-calls.mdx:459,605),
so the race excuse does not apply and the missing methods are not hidden: FAILs
`ACP-TOOLCANCEL-201` and `ACP-TERMCANCEL-201` (`-202` SKIP: nothing was accepted). Within the
`-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from races_cancel_with_completion import RacesCancelWithCompletionAgent  # noqa: E402


class CancelMissingAfterCompletionAgent(RacesCancelWithCompletionAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32601, "Method not found")

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32601, "Method not found")


def main() -> None:
    CancelMissingAfterCompletionAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
