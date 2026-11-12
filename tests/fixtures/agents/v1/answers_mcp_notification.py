#!/usr/bin/env python3
"""Non-conforming fixture: advertises `agentCapabilities.mcpCapabilities.acp` and replies `-32602`
(with `id: null`) to an `mcp/message` notification instead of staying silent, as a dedicated
MCP-over-ACP handler that validates the envelope might. Other notifications are ignored. Violates
ACP-JSONRPC-003 only -- notifications never receive a response (overview.mdx:239).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersMcpNotificationAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "mcp/message":
            self._error(None, -32602, "Invalid params")
            return
        super()._handle_notification(method, params)


def main() -> None:
    AnswersMcpNotificationAgent(capabilities={"mcpCapabilities": {"acp": True}}).run()


if __name__ == "__main__":
    main()
