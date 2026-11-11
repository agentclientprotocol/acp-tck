#!/usr/bin/env python3
"""Non-conforming fixture: an agent that does not keep a session it was never prompted in
(session-setup.mdx:47 allows that) but discards it even while it is active: a `session/resume`
without `replayFrom` for a session with no history answers `-32002`. A session that has been
prompted, or was closed, resumes normally, so every other resume row still runs.

FAILs exactly `ACP-RESUME-216` (ADVISORY). `ACP-RESUME-210` SKIPs: its resume of the
just-created session errors.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeRejectsUnpromptedActiveSessionAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        unprompted = session_id in self._sessions and not self._history.get(session_id)
        if unprompted and params.get("replayFrom") is None:
            self._unknown_session(msg_id, session_id)
            return
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    ResumeRejectsUnpromptedActiveSessionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
