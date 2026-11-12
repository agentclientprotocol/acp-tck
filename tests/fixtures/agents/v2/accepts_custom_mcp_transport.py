#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` accepts an MCP server of any `_`-prefixed (custom)
transport it never advertised, while still rejecting `sse` (session-setup.mdx:545,553). FAILs
exactly `ACP-MCP-203` (its `_tck_unsupported_transport` probe).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsCustomMcpTransportAgent(ConformingAgent):
    def _mcp_transport_rejection(self, servers: Any) -> str | None:
        if isinstance(servers, list):
            servers = [
                s
                for s in servers
                if not (isinstance(s, dict) and str(s.get("type", "")).startswith("_"))
            ]
        return super()._mcp_transport_rejection(servers)


def main() -> None:
    AcceptsCustomMcpTransportAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
