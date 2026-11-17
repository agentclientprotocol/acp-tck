#!/usr/bin/env python3
"""Non-conforming fixture: like `conforming_full.py`, a `__hang__` turn starts a cancellable tool
call and terminal and a live tool call and terminal that advertise no `cancel`, but
`tool_call/cancel` for the tool call without `cancel` is rejected with `-32603` instead of
`-32602` (tool-calls.mdx:459). The rejection itself is right, so FAILs exactly the ADVISORY
`ACP-TOOLCANCEL-209`. Within the `-k` scope of the `test_item_controls.py` module, with
`--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UncancellableToolCallCancelWrongCodeAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if str(params.get("toolCallId", "")).startswith("tool-fixed-"):
            self._error(msg_id, -32603, "Internal error")  # a tool call that does not advertise `cancel`
            return
        super()._handle_tool_call_cancel(msg_id, params)


def main() -> None:
    UncancellableToolCallCancelWrongCodeAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
