#!/usr/bin/env python3
"""Hazard fixture for `obtain_resumable_session`'s `session/list` route: stands in for an agent
that persists the operator's own sessions. `session/list` ignores the `cwd` filter and always
reports one saved session under a foreign `cwd` (`/operator/saved-project`); `session/resume`
accepts only that session and rejects every id the TCK itself creates.

A TCK that resumed the first listed entry would "succeed" on the operator's session and go on to
prompt into it. The correct TCK skips any entry not under its own `cwd`, so no route succeeds and
every resume-dependent test SKIPs, never touching `operator-sess`.

Ignoring the `cwd` filter is itself non-conforming, so `ACP-LIST-202`/`203` FAIL here.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

FOREIGN_SESSION_ID = "operator-sess"
FOREIGN_CWD = "/operator/saved-project"


class ResumeListsForeignSessionAgent(ConformingAgent):
    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"sessions": [{"sessionId": FOREIGN_SESSION_ID, "cwd": FOREIGN_CWD}]})

    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("sessionId") != FOREIGN_SESSION_ID:
            self._error(msg_id, -32602, "Invalid params: unknown session")
            return
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    ResumeListsForeignSessionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
