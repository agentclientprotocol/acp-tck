#!/usr/bin/env python3
"""Non-conforming fixture: a `tool_call/cancel` sent again for a tool call it already accepted a
cancel for, and whose final `cancelled` status (with `capabilities` cleared) was reported, is
answered with an empty result instead of `-32602`. The agent responds with an error for a request
that the Client sends again after the first one was accepted and the tool call has since reached
a final status (tool-calls.mdx:459): FAILs exactly `ACP-TOOLCANCEL-210` (`-211` SKIPs: nothing was
rejected). Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt
__hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RepeatToolCancelAcceptedAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        item_id = str(params.get("toolCallId", ""))
        if item_id.startswith("tool-live-") and item_id not in self._open_tool_calls.get(params.get("sessionId"), []):
            self._reply(msg_id, {})  # already cancelled and final: should be -32602
            return
        super()._handle_tool_call_cancel(msg_id, params)


def main() -> None:
    RepeatToolCancelAcceptedAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
