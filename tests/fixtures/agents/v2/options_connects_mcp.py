#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and `mcp.stdio`, and
`session/options` with a `sessionId` reconnects to the MCP servers the session was created with.
Violates ACP-OPTIONS-009 (ADVISORY) only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"options": {}, "mcp": {"stdio": {}}}}


class OptionsConnectsMcpAgent(ConformingAgent):
    _servers: dict[Any, list[Any]] = {}  # sessionId -> the mcpServers it was created with

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_new_session(msg_id, params)
        self._servers[f"sess-{self._session_count:04d}"] = params.get("mcpServers") or []

    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._launch_mcp_servers(self._servers.get(params.get("sessionId"), []))
        super()._handle_options(msg_id, params)


def main() -> None:
    OptionsConnectsMcpAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-options-connects-mcp").run()


if __name__ == "__main__":
    main()
