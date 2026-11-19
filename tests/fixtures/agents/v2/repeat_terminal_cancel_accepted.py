#!/usr/bin/env python3
"""Non-conforming fixture: a `terminal/cancel` sent again for a terminal it already accepted a
cancel for, and whose `exitStatus` (with `capabilities` cleared) was reported, is answered with an
empty result instead of `-32602`. The agent responds with an error for a request that the Client
sends again after the first one was accepted and the process has since exited (tool-calls.mdx:605):
FAILs exactly `ACP-TERMCANCEL-210` (`-211` SKIPs: nothing was rejected). Within the `-k` scope of
the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RepeatTerminalCancelAcceptedAgent(ConformingAgent):
    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        item_id = str(params.get("terminalId", ""))
        if item_id.startswith("term-live-") and item_id not in self._open_terminals.get(params.get("sessionId"), []):
            self._reply(msg_id, {})  # already cancelled and exited: should be -32602
            return
        super()._handle_terminal_cancel(msg_id, params)


def main() -> None:
    RepeatTerminalCancelAcceptedAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
