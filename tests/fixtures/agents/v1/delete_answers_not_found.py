#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.list`, `.delete` and `.close`, and
answers `session/delete` for a session it no longer holds with `-32002` + `data.sessionId`
(closing already discarded it) instead of the empty result. Trips ACP-DELETE-001 (the delete of
the just-closed session is an error) and ACP-DELETE-002 (advisory: the unknown id is an error).
ACP-DELETE-003 still PASSes: clients treat `-32002` as a successful delete, so it goes on to
check that the session is absent from `session/list`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "close": {}}}


class DeleteAnswersNotFoundAgent(ConformingAgent):
    def _handle_delete(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions:
            self._unknown_session(msg_id, session_id)
            return
        super()._handle_delete(msg_id, params)


def main() -> None:
    DeleteAnswersNotFoundAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-delete-answers-not-found"
    ).run()


if __name__ == "__main__":
    main()
