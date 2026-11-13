#!/usr/bin/env python3
"""Non-conforming fixture: `cancellable_subagent.py`, except that `tool_call/cancel` for the child's
live tool call (which advertises `capabilities.cancel`; the child itself does not) is answered with
an error instead of an empty result (tool-calls.mdx:457-458). FAILs exactly
`ACP-TOOLCANCEL-203`; the terminal row still PASSes. Within the `-k` scope of the
`test_subagent_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancellable_subagent import CancellableSubagentAgent  # noqa: E402


class ChildToolCallCancelErrorsAgent(CancellableSubagentAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error")


def main() -> None:
    ChildToolCallCancelErrorsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
