#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.mcp.acp` and replies `-32602` (with
`id: null`) to a malformed `mcp/message` notification (no `requestId`) instead of staying silent,
as a handler that validates the envelope and reports the failure might (the Active MCP-over-ACP
RFD says malformed notifications get no synthetic reply). The well-formed probe and other
notifications are ignored. Violates ACP-JSONRPC-003 only, through its malformed probe --
notifications never receive a response (overview.mdx:227).

v2's `_base.py` has no notification hook, so this overrides `_handle` for the one method.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersMalformedMcpNotificationAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        params = message.get("params")
        malformed = isinstance(params, dict) and "requestId" not in params
        if message.get("method") == "mcp/message" and "id" not in message and malformed:
            self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32602, "message": "Invalid params"}})
            return
        super()._handle(message)


def main() -> None:
    AnswersMalformedMcpNotificationAgent(capabilities={"session": {"mcp": {"acp": {}}}}).run()


if __name__ == "__main__":
    main()
