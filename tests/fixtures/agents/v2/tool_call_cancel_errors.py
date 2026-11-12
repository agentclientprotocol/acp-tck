#!/usr/bin/env python3
"""Non-conforming fixture: its tool call advertises `capabilities.cancel` and is still running,
but `tool_call/cancel` for it is answered with an error instead of an empty result once
accepted (tool-calls.mdx:458): FAILs exactly `ACP-TOOLCANCEL-201`. `ACP-TOOLCANCEL-202`
judges only an accepted cancel, so it SKIPs. Within the `-k` scope of the `test_item_controls.py`
module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ToolCallCancelErrorsAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error")


def main() -> None:
    ToolCallCancelErrorsAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
