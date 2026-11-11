#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive`, but errors when archiving an
already-archived session or unarchiving one that is not archived, instead of succeeding.
FAILs exactly `ACP-ARCHIVE-005`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveNotIdempotentAgent(ConformingAgent):
    def _handle_archive_session(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        session_id = params.get("sessionId")
        known = session_id in self._sessions or session_id in self._closed_sessions
        if known and archived == (session_id in self._archived):
            self._error(msg_id, -32603, "Internal error: archive state already set")
            return
        super()._handle_archive_session(msg_id, params, archived=archived)


def main() -> None:
    ArchiveNotIdempotentAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-not-idempotent"
    ).run()


if __name__ == "__main__":
    main()
