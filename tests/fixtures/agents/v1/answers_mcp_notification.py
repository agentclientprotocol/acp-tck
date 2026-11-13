#!/usr/bin/env python3
"""Non-conforming fixture: advertises `agentCapabilities.mcpCapabilities.acp` and replies `-32602` (with
`id: null`) to a well-formed `mcp/message` notification (one carrying `requestId` and `method`)
instead of staying silent, as a dedicated MCP-over-ACP handler might. The malformed probe and other
notifications are ignored. Violates ACP-JSONRPC-003 only, through its well-formed probe --
notifications never receive a response (overview.mdx:239).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersMcpNotificationAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "mcp/message" and isinstance(params, dict) and "requestId" in params:
            self._error(None, -32602, "Invalid params")
            return
        super()._handle_notification(method, params)


def main() -> None:
    AnswersMcpNotificationAgent(capabilities={"mcpCapabilities": {"acp": True}}).run()


if __name__ == "__main__":
    main()
