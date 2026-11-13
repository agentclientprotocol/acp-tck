#!/usr/bin/env python3
"""Non-conforming fixture: advertises `agentCapabilities.mcpCapabilities.acp` and replies `-32602` (with
`id: null`) to a malformed `mcp/message` notification (no `requestId`) instead of staying silent,
as a handler that validates the envelope and reports the failure might (the Active MCP-over-ACP
RFD says malformed notifications get no synthetic reply). The well-formed probe and other
notifications are ignored. Violates ACP-JSONRPC-003 only, through its malformed probe --
notifications never receive a response (overview.mdx:239).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersMalformedMcpNotificationAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "mcp/message" and isinstance(params, dict) and "requestId" not in params:
            self._error(None, -32602, "Invalid params")
            return
        super()._handle_notification(method, params)


def main() -> None:
    AnswersMalformedMcpNotificationAgent(capabilities={"mcpCapabilities": {"acp": True}}).run()


if __name__ == "__main__":
    main()
