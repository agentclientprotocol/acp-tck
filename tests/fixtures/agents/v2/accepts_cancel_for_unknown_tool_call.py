#!/usr/bin/env python3
"""Non-conforming fixture: its tool call advertises `capabilities.cancel` and is cancelled like
`conforming_full.py`'s, but `tool_call/cancel` for a `toolCallId` it never announced is answered
with an empty result instead of an error. The agent responds with an error for an unknown tool
call (tool-calls.mdx:459): FAILs exactly `ACP-TOOLCANCEL-206` (`-207` SKIPs: nothing was
rejected). Within the `-k` scope of the `test_item_controls.py` module, with `--cancel-prompt
__hang__`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsCancelForUnknownToolCallAgent(ConformingAgent):
    def _handle_tool_call_cancel(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not str(params.get("toolCallId", "")).startswith("tool-live-"):
            self._reply(msg_id, {})  # an id this agent never announced
            return
        super()._handle_tool_call_cancel(msg_id, params)


def main() -> None:
    AcceptsCancelForUnknownToolCallAgent(capabilities={"session": {}}, cancellable_work=True).run()


if __name__ == "__main__":
    main()
