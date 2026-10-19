#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: accepts stdio `mcpServers` on `session/new` but never
launches them. Violates ACP-SESSION-004 only (agents SHOULD connect to every MCP server the
client specifies); ACP-SESSION-003 still PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class IgnoresMcpServersAgent(ConformingAgent):
    def _launch_mcp_servers(self, servers: list[Any]) -> None:
        pass


def main() -> None:
    IgnoresMcpServersAgent(agent_name="tck-fixture-ignores-mcp-servers").run()


if __name__ == "__main__":
    main()
