#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.mcp.acp` and replies `-32602` (with
`id: null`) to a well-formed `mcp/message` notification (one carrying `requestId` and `method`)
instead of staying silent, as a dedicated MCP-over-ACP handler might. The malformed probe and other
notifications are ignored. Violates ACP-JSONRPC-003 only, through its well-formed probe --
notifications never receive a response (overview.mdx:227).

v2's `_base.py` has no notification hook, so this overrides `_handle` for the one method.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersMcpNotificationAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        params = message.get("params")
        well_formed = isinstance(params, dict) and "requestId" in params
        if message.get("method") == "mcp/message" and "id" not in message and well_formed:
            self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32602, "message": "Invalid params"}})
            return
        super()._handle(message)


def main() -> None:
    AnswersMcpNotificationAgent(capabilities={"session": {"mcp": {"acp": {}}}}).run()


if __name__ == "__main__":
    main()
