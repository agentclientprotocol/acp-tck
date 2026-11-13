#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` accepts an MCP server of the unstable `acp` transport
although it never advertises `capabilities.session.mcp.acp`, while still rejecting `sse` and
every other unsupported transport with `-32602` (session-setup.mdx:545). FAILs exactly
`ACP-MCP-203` (its `acp` probe).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsUnadvertisedAcpMcpAgent(ConformingAgent):
    def _mcp_transport_rejection(self, servers: Any) -> str | None:
        if isinstance(servers, list):
            servers = [s for s in servers if not (isinstance(s, dict) and s.get("type") == "acp")]
        return super()._mcp_transport_rejection(servers)


def main() -> None:
    AcceptsUnadvertisedAcpMcpAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
