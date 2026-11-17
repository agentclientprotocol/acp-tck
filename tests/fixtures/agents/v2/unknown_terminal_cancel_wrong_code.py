#!/usr/bin/env python3
"""Non-conforming fixture: its terminal advertises `capabilities.cancel` and is cancelled like
`conforming_full.py`'s, but `terminal/cancel` for a `terminalId` it never announced is rejected
with `-32603` instead of `-32602` (tool-calls.mdx:605). The rejection itself is right, so FAILs
exactly the ADVISORY `ACP-TERMCANCEL-207`. Within the `-k` scope of the `test_item_controls.py`
module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnknownTerminalCancelWrongCodeAgent(ConformingAgent):
    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not str(params.get("terminalId", "")).startswith("term-live-"):
            self._error(msg_id, -32603, "Internal error")  # an id this agent never announced
            return
        super()._handle_terminal_cancel(msg_id, params)


def main() -> None:
    UnknownTerminalCancelWrongCodeAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
