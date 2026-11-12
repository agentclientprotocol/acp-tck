#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.mcp.acp` and replies `-32602` (with
`id: null`) to an `mcp/message` notification instead of staying silent, as a dedicated
MCP-over-ACP handler that validates the envelope might. Other notifications are ignored. Violates
ACP-JSONRPC-003 only -- notifications never receive a response (overview.mdx:227).

v2's `_base.py` has no notification hook, so this overrides `_handle` for the one method.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersMcpNotificationAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        if message.get("method") == "mcp/message" and "id" not in message:
            self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32602, "message": "Invalid params"}})
            return
        super()._handle(message)


def main() -> None:
    AnswersMcpNotificationAgent(capabilities={"session": {"mcp": {"acp": {}}}}).run()


if __name__ == "__main__":
    main()
