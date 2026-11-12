#!/usr/bin/env python3
"""Non-conforming fixture: `terminal/cancel` for its advertised, running terminal is answered
with an empty result, but no `terminal_update` sets `exitStatus` in response (it is only
finalized when the turn ends). The Agent confirms an accepted cancel with a `terminal_update`
that sets `exitStatus` (tool-calls.mdx:604): FAILs exactly `ACP-TERMCANCEL-202`. Within the
`-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class TerminalCancelNeverExitsAgent(ConformingAgent):
    def _confirm_terminal_cancel(self, session_id: Any, terminal_id: str) -> None:
        pass


def main() -> None:
    TerminalCancelNeverExitsAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
