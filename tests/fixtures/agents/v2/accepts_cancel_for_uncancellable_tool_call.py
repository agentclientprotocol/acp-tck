#!/usr/bin/env python3
"""Non-conforming fixture: like `conforming_full.py`, a `__hang__` turn starts a cancellable tool
call and terminal and a live tool call and terminal that advertise no `cancel`, but
`tool_call/cancel` for the tool call without `cancel` is answered with an empty result instead of
an error. The agent responds with an error for a tool call that is not cancellable
(tool-calls.mdx:459): FAILs exactly `ACP-TOOLCANCEL-208` (`-209` SKIPs: nothing was rejected).
Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsCancelForUncancellableToolCallAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if str(params.get("toolCallId", "")).startswith("tool-fixed-"):
            self._reply(msg_id, {})  # a live tool call that does not advertise `cancel`
            return
        super()._handle_tool_call_cancel(msg_id, params)


def main() -> None:
    AcceptsCancelForUncancellableToolCallAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
