#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.delete` and deletes the session, but
leaves a still-hanging `__hang__` turn running instead of cancelling it as `session/close` would.

Only observable with `--cancel-prompt __hang__`; every other prompt finishes normally. FAILs
exactly `ACP-DELETE-204` (the turn never ends, so the TCK's wait times out). `ACP-DELETE-001`
(idle session), `ACP-DELETE-003` and `ACP-DELETE-205` PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class DeleteDoesNotCancelActiveAgent(ConformingAgent):
    def _handle_delete_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        self._sessions.pop(session_id, None)
        self._closed_sessions.pop(session_id, None)
        self._reply(msg_id, {})


def main() -> None:
    DeleteDoesNotCancelActiveAgent(capabilities={"session": {"delete": {}}}).run()


if __name__ == "__main__":
    main()
