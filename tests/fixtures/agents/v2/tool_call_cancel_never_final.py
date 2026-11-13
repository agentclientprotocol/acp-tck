#!/usr/bin/env python3
"""Non-conforming fixture: `tool_call/cancel` for its advertised, running tool call is answered
with an empty result, but the tool call never gets a final status in response (it is only
finalized when the turn ends). The Agent confirms an accepted cancel with a `tool_call_update`
to a final status (tool-calls.mdx:458): FAILs exactly `ACP-TOOLCANCEL-202`. Within the `-k`
scope of the `test_item_controls.py` module, with `--cancel-prompt __hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ToolCallCancelNeverFinalAgent(ConformingAgent):
    def _confirm_tool_call_cancel(self, session_id: Any, tool_call_id: str) -> None:
        pass


def main() -> None:
    ToolCallCancelNeverFinalAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
