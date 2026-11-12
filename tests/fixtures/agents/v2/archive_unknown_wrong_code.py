#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive` and fails
`session/archive`/`session/unarchive` for a session that does not exist, but with `-32602` rather
than the `-32002` the docs name (error.mdx:66). FAILs exactly `ACP-ARCHIVE-005`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveUnknownWrongCodeAgent(ConformingAgent):
    def _handle_archive_session(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            self._error(msg_id, -32602, "Invalid params: unknown session", {"sessionId": session_id})
            return
        super()._handle_archive_session(msg_id, params, archived=archived)


def main() -> None:
    ArchiveUnknownWrongCodeAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-unknown-wrong-code"
    ).run()


if __name__ == "__main__":
    main()
