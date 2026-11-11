#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive` and answers `session/archive`
with `{}` (closing the session, so in-flight work is still cancelled), but never records it as
archived: it keeps appearing in the default `session/list` view and never under `archived: "only"`.
FAILs exactly `ACP-ARCHIVE-003`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveStillListedAgent(ConformingAgent):
    def _handle_archive_session(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            self._unknown_session(msg_id, session_id)
            return
        if archived:
            self._close_for_archive(session_id)
        self._reply(msg_id, {})


def main() -> None:
    ArchiveStillListedAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-archive-still-listed").run()


if __name__ == "__main__":
    main()
