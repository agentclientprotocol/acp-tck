#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.archive` and `.delete`, but lists a session
only after its first prompt (as some real agents do). The archive and delete views cannot be
compared for a fresh session, so `ACP-ARCHIVE-002`, `-003` and `-006` SKIP rather than PASS
vacuously.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveListsNothingUnpromptedAgent(ConformingAgent):
    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        hidden_live = {k: v for k, v in self._sessions.items() if k not in self._history}
        hidden_closed = {k: v for k, v in self._closed_sessions.items() if k not in self._history}
        for session_id in hidden_live:
            del self._sessions[session_id]
        for session_id in hidden_closed:
            del self._closed_sessions[session_id]
        try:
            super()._handle_list_sessions(msg_id, params)
        finally:
            self._sessions.update(hidden_live)
            self._closed_sessions.update(hidden_closed)


def main() -> None:
    ArchiveListsNothingUnpromptedAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-lists-nothing-unprompted"
    ).run()


if __name__ == "__main__":
    main()
