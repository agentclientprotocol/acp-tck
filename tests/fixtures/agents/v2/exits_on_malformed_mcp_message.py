#!/usr/bin/env python3
"""Non-conforming fixture: does not advertise `capabilities.session.mcp.acp` and
exits the process on an `mcp/message` notification that is missing `requestId`, as an agent that
cannot parse an envelope it does not know might crash. It never replies, so ACP-JSONRPC-003
(only a reply fails it) PASSes; ACP-EXT-002 judges the crash on a notification the agent does not
recognize (SHOULD ignore it) and FAILs, alone.

v2's `_base.py` has no notification hook, so this overrides `_handle` for the one method.
"""

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ExitsOnMalformedMcpMessageAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        params = message.get("params")
        malformed = isinstance(params, dict) and "requestId" not in params
        if message.get("method") == "mcp/message" and "id" not in message and malformed:
            os._exit(1)
        super()._handle(message)


def main() -> None:
    ExitsOnMalformedMcpMessageAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
