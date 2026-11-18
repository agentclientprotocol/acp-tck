#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options`, `loadSession` and persists
sessions across processes, and `session/options` with a `sessionId` reconnects to the MCP servers
the session was created with. Violates ACP-OPTIONS-009 (ADVISORY) only.
"""

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"options": {}}}


class OptionsConnectsMcpAgent(ConformingAgent):
    _persist_sessions = True

    def _servers_path(self, cwd: Any) -> Path:
        return Path(cwd) / ".tck-fixture-mcp-servers.json"

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_new_session(msg_id, params)
        if isinstance(params.get("cwd"), str):
            session_id = f"sess-{self._session_count:04d}"
            path = self._servers_path(params["cwd"])
            path.write_text(json.dumps({session_id: params.get("mcpServers") or []}))

    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id is not None and isinstance(params.get("cwd"), str):
            try:
                stored = json.loads(self._servers_path(params["cwd"]).read_text())
            except (OSError, ValueError):
                stored = {}
            self._launch_mcp_servers(stored.get(session_id) or [])
        super()._handle_options(msg_id, params)


def main() -> None:
    OptionsConnectsMcpAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-options-connects-mcp").run()


if __name__ == "__main__":
    main()
