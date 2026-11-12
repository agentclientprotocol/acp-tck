#!/usr/bin/env python3
"""Non-conforming fixture: advertises `session.mcp.stdio` but accepts two MCP servers sharing a
`name` instead of rejecting them with `-32602` (session-setup.mdx:547). FAILs exactly
`ACP-MCP-204` (ADVISORY).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsDuplicateMcpNamesAgent(ConformingAgent):
    @staticmethod
    def _mcp_duplicate_name_rejection(servers: Any) -> str | None:
        return None


def main() -> None:
    AcceptsDuplicateMcpNamesAgent(capabilities={"session": {"mcp": {"stdio": {}}}}).run()


if __name__ == "__main__":
    main()
