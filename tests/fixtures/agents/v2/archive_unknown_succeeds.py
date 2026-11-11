#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive`, but answers
`session/archive`/`session/unarchive` for a session that does not exist with `{}` (the way
`session/delete` does) instead of `-32002`. FAILs exactly `ACP-ARCHIVE-005`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveUnknownSucceedsAgent(ConformingAgent):
    def _handle_archive_session(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            self._reply(msg_id, {})
            return
        super()._handle_archive_session(msg_id, params, archived=archived)


def main() -> None:
    ArchiveUnknownSucceedsAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-unknown-succeeds"
    ).run()


if __name__ == "__main__":
    main()
