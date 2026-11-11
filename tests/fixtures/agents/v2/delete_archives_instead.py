#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive` and `.delete`, but implements
`session/delete` as an archive: the session can no longer be resumed and leaves the default
`session/list` view, yet still shows under `archived: "include"` and `"only"`. FAILs exactly
`ACP-ARCHIVE-006`; `ACP-DELETE-202` (default view) and `-205` (resume) still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class DeleteArchivesInsteadAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._shadow: dict[str, str] = {}  # "deleted" sessionId -> cwd, still archived and listed

    def _handle_delete_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        self._close_for_archive(session_id)
        cwd = self._closed_sessions.pop(session_id, None)
        if cwd is not None:
            self._shadow[session_id] = cwd
            self._archived.add(session_id)
        self._reply(msg_id, {})

    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._closed_sessions.update(self._shadow)
        try:
            super()._handle_list_sessions(msg_id, params)
        finally:
            for session_id in self._shadow:
                self._closed_sessions.pop(session_id, None)


def main() -> None:
    DeleteArchivesInsteadAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-delete-archives-instead"
    ).run()


if __name__ == "__main__":
    main()
