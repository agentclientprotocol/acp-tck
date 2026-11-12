#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive`, `.list` and `.delete`, but
implements `session/delete` as an archive: the session leaves the default `session/list` view
yet still shows under `archived: "include"` and `"only"`. Violates ACP-ARCHIVE-006 only;
ACP-DELETE-003 (default view) still PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class DeleteArchivesInsteadAgent(ConformingAgent):
    def _handle_delete(self, msg_id: Any, params: dict[str, Any]) -> None:
        session = self._sessions.get(params.get("sessionId"))
        if session is not None:
            session["archived"] = True
        self._reply(msg_id, {})


def main() -> None:
    DeleteArchivesInsteadAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-delete-archives-instead"
    ).run()


if __name__ == "__main__":
    main()
