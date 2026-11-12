#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive` and answers
`session/archive` with `{}`, but the session is not archived: it keeps appearing in the default
`session/list` view and never under `archived: "only"`. Violates ACP-ARCHIVE-003 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class ArchiveStillListedAgent(ConformingAgent):
    def _handle_archive(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        if params.get("sessionId") not in self._sessions:
            self._unknown_session(msg_id, params.get("sessionId"))
            return
        self._reply(msg_id, {})


def main() -> None:
    ArchiveStillListedAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-archive-still-listed").run()


if __name__ == "__main__":
    main()
