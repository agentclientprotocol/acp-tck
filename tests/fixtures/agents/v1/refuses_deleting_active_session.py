#!/usr/bin/env python3
"""A conforming fixture: advertises `sessionCapabilities.delete` and `.list` but not `close`,
and refuses to delete a session that is still active on this connection. The spec leaves
deleting an active session implementation-defined, so ACP-DELETE-001/003 SKIP rather than FAIL;
deleting an unknown id still succeeds silently (ACP-DELETE-002 PASSes).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}}}


class RefusesDeletingActiveSessionAgent(ConformingAgent):
    def _handle_delete(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("sessionId") in self._sessions:
            self._error(msg_id, -32603, "Cannot delete an active session")
            return
        super()._handle_delete(msg_id, params)


def main() -> None:
    RefusesDeletingActiveSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-refuses-deleting-active-session"
    ).run()


if __name__ == "__main__":
    main()
