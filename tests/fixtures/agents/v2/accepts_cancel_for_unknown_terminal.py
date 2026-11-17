#!/usr/bin/env python3
"""Non-conforming fixture: its terminal advertises `capabilities.cancel` and is cancelled like
`conforming_full.py`'s, but `terminal/cancel` for a `terminalId` it never announced is answered
with an empty result instead of an error. The agent responds with an error for an unknown terminal
(tool-calls.mdx:605): FAILs exactly `ACP-TERMCANCEL-206` (`-207` SKIPs: nothing was rejected).
Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsCancelForUnknownTerminalAgent(ConformingAgent):
    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not str(params.get("terminalId", "")).startswith("term-live-"):
            self._reply(msg_id, {})  # an id this agent never announced
            return
        super()._handle_terminal_cancel(msg_id, params)


def main() -> None:
    AcceptsCancelForUnknownTerminalAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
