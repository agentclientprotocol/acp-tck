#!/usr/bin/env python3
"""Non-conforming fixture: its terminal advertises `capabilities.cancel` and is still running,
but `terminal/cancel` for it is answered `-32602` (as for an exited terminal, tool-calls.mdx:605)
and the terminal neither exits nor stops advertising `cancel`. `-32602` is only the right answer
for a terminal that is no longer cancellable, so it is a rejection, judged once the grace window
for an `exitStatus` or a withdrawal of `cancel` has passed: FAILs exactly `ACP-TERMCANCEL-201`.
`ACP-TERMCANCEL-202` judges only an accepted cancel, so it SKIPs. Within the `-k` scope of the
`test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class TerminalCancelErrorsAgent(ConformingAgent):
    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32602, "Invalid params")


def main() -> None:
    TerminalCancelErrorsAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
