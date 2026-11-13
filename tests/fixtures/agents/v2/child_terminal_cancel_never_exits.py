#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that `terminal/cancel` for the child's
running terminal is accepted with an empty result but the terminal never gets an `exitStatus`
(tool-calls.mdx:603-604). FAILs exactly `ACP-TERMCANCEL-203`; the tool call row still PASSes.
Within the `-k` scope of the `test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildTerminalCancelNeverExitsAgent(CancellableSubagentAgent):
    def _confirm_terminal_cancel(self, session_id: Any, terminal_id: str) -> None:
        pass


def main() -> None:
    ChildTerminalCancelNeverExitsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
