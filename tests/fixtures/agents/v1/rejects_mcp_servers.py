#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` errors whenever `mcpServers` is non-empty, i.e. it does
not support the stdio MCP transport every agent MUST support. Violates ACP-SESSION-003 only;
ACP-SESSION-004 SKIPs on the failed prerequisite.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsMcpServersAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("mcpServers"):
            self._error(msg_id, -32602, "Invalid params: MCP servers are not supported")
            return
        super()._handle_new_session(msg_id, params)


def main() -> None:
    RejectsMcpServersAgent(agent_name="tck-fixture-rejects-mcp-servers").run()


if __name__ == "__main__":
    main()
