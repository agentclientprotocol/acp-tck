#!/usr/bin/env python3
"""Conforming fixture for the not-cancellable cancel rows: like `conforming_full.py`, a `__hang__`
turn starts a live tool call and terminal that advertise no `cancel`. When `tool_call/cancel` or
`terminal/cancel` for one of them arrives, the item has just finished: the agent sends its final
status (`exitStatus`) and only then answers `-32602`, as tool-calls.mdx:459,605 require for an item
that is already final. The item finished before the response, yet the answer is the same one a
not-cancellable item gets, so `ACP-TOOLCANCEL-208/209` and `ACP-TERMCANCEL-208/209` PASS and nothing
FAILs. Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UncancellableFinishesFirstAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if str(params.get("toolCallId", "")).startswith("tool-fixed-"):
            self._finish_fixed_item(params.get("sessionId"), str(params.get("toolCallId")))
        super()._handle_tool_call_cancel(msg_id, params)  # `-32602`: no longer open

    def _handle_terminal_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if str(params.get("terminalId", "")).startswith("term-fixed-"):
            self._finish_fixed_item(params.get("sessionId"), str(params.get("terminalId")))
        super()._handle_terminal_cancel(msg_id, params)


def main() -> None:
    UncancellableFinishesFirstAgent(
        capabilities={"session": {}}, cancellable_work=True, uncancellable_work=True
    ).run()


if __name__ == "__main__":
    main()
