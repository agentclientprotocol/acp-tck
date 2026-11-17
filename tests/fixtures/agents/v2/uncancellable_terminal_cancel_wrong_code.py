#!/usr/bin/env python3
"""Non-conforming fixture: like `conforming_full.py`, a `__hang__` turn starts a cancellable tool
call and terminal and a live tool call and terminal that advertise no `cancel`, but
`terminal/cancel` for the terminal without `cancel` is rejected with `-32603` instead of `-32602`
(tool-calls.mdx:605). The rejection itself is right, so FAILs exactly the ADVISORY
`ACP-TERMCANCEL-209`. Within the `-k` scope of the `test_item_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UncancellableTerminalCancelWrongCodeAgent(ConformingAgent):
    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if str(params.get("terminalId", "")).startswith("term-fixed-"):
            self._error(msg_id, -32603, "Internal error")  # a terminal that does not advertise `cancel`
            return
        super()._handle_terminal_cancel(msg_id, params)


def main() -> None:
    UncancellableTerminalCancelWrongCodeAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
