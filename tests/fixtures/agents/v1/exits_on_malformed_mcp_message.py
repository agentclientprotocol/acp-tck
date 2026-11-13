#!/usr/bin/env python3
"""Non-conforming fixture: does not advertise `agentCapabilities.mcpCapabilities.acp` and
exits the process on an `mcp/message` notification that is missing `requestId`, as an agent that
cannot parse an envelope it does not know might crash. It never replies, so ACP-JSONRPC-003
(only a reply fails it) PASSes; ACP-EXT-002 judges the crash on a notification the agent does not
recognize (SHOULD ignore it) and FAILs, alone.
"""

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ExitsOnMalformedMcpMessageAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "mcp/message" and isinstance(params, dict) and "requestId" not in params:
            os._exit(1)
        super()._handle_notification(method, params)


def main() -> None:
    ExitsOnMalformedMcpMessageAgent().run()


if __name__ == "__main__":
    main()
