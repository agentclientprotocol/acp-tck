#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` accepts an MCP server of v1's `sse` transport, which no
v2 agent supports (session-setup.mdx:545); every other unsupported transport is still rejected
with `-32602`. FAILs exactly `ACP-MCP-203` (its `sse` probe).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsSseMcpAgent(ConformingAgent):
    def _mcp_transport_rejection(self, servers: Any) -> str | None:
        if isinstance(servers, list):
            servers = [s for s in servers if not (isinstance(s, dict) and s.get("type") == "sse")]
        return super()._mcp_transport_rejection(servers)


def main() -> None:
    AcceptsSseMcpAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
