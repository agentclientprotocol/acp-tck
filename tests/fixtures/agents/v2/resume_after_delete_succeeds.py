#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.delete`; `session/delete` removes the
session from `session/list`, but `session/resume` of a deleted id still succeeds instead of
answering `-32002`.

FAILs exactly `ACP-DELETE-205`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeAfterDeleteSucceedsAgent(ConformingAgent):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._deleted: dict[str, str] = {}  # deleted sessionId -> cwd

    def _handle_delete_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        cwd = self._sessions.get(session_id) or self._closed_sessions.get(session_id)
        if cwd is not None:
            self._deleted[session_id] = cwd
        super()._handle_delete_session(msg_id, params)

    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id in self._deleted:
            self._sessions[session_id] = self._deleted.pop(session_id)
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    ResumeAfterDeleteSucceedsAgent(capabilities={"session": {"delete": {}}}).run()


if __name__ == "__main__":
    main()
