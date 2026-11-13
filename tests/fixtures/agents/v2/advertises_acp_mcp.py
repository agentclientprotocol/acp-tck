#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.mcp.acp` and so accepts an `acp` MCP
server declaration. `ACP-MCP-203` must therefore not send its `acp` probe, which this agent would
accept (session-setup.mdx:545); the run has no FAIL.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(capabilities={"session": {"mcp": {"acp": {}}}}).run()


if __name__ == "__main__":
    main()
