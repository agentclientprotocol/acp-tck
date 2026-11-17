#!/usr/bin/env python3
"""Non-conforming fixture: its tool call advertises `capabilities.cancel` and is cancelled like
`conforming_full.py`'s, but `tool_call/cancel` for a `toolCallId` it never announced is rejected
with `-32603` instead of `-32602` (tool-calls.mdx:459). The rejection itself is right, so FAILs
exactly the ADVISORY `ACP-TOOLCANCEL-207`. Within the `-k` scope of the `test_item_controls.py`
module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnknownToolCallCancelWrongCodeAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not str(params.get("toolCallId", "")).startswith("tool-live-"):
            self._error(msg_id, -32603, "Internal error")  # an id this agent never announced
            return
        super()._handle_tool_call_cancel(msg_id, params)


def main() -> None:
    UnknownToolCallCancelWrongCodeAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
