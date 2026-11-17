#!/usr/bin/env python3
"""Conforming fixture: its tool call and terminal advertise `capabilities.cancel` while live. When
the request arrives it answers `-32602` and then stops advertising `cancel` (`capabilities:
null`) while the item is still running, as an agent whose cancellation window closed as the
request crossed the update (tool-calls.mdx:440,459,605). The `-32602` is not a rejection, so
`ACP-TOOLCANCEL-*` and `ACP-TERMCANCEL-*` SKIP and nothing FAILs, except the unknown-id rows
(`-206/207`), which PASS. The withdrawal leaves the items live without `cancel`, but the TCK
already sent them a request, so the not-cancellable rows (`-208/209`) have no target and SKIP.
Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class WithdrawsCancelOnRequestAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not str(params.get("toolCallId", "")).startswith("tool-live-"):
            super()._handle_tool_call_cancel(msg_id, params)  # `-32602` for an unknown id
            return
        self._error(msg_id, -32602, "Tool call is no longer cancellable")
        self._send_update(
            params.get("sessionId"),
            {"sessionUpdate": "tool_call_update", "toolCallId": params.get("toolCallId"), "capabilities": None},
        )

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not str(params.get("terminalId", "")).startswith("term-live-"):
            super()._handle_terminal_cancel(msg_id, params)
            return
        self._error(msg_id, -32602, "Terminal is no longer cancellable")
        self._send_update(
            params.get("sessionId"),
            {"sessionUpdate": "terminal_update", "terminalId": params.get("terminalId"), "capabilities": None},
        )


def main() -> None:
    WithdrawsCancelOnRequestAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
