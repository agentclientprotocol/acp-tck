#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session: {}` (the baseline) but
`session/resume` of a session this connection holds (live or closed) always errors with a
non-`-32601` code, whatever route obtained it. An unknown id still gets the conforming `-32002`.

Self-test for `obtain_resumable_session`'s all-three-routes-exhausted SKIP behavior:
`obtain_resumable_session`'s three routes (create-then-resume, close-then-resume,
list-then-resume) all end in the same `session/resume` call, so all three fail identically here
-- with a plain `-32603`, never `-32601` (Method not found, which would instead be a hard
`pytest.fail`). `obtain_resumable_session` must exhaust all three routes and then
`pytest.skip(...)`, and every test that routes through it (`ACP-RESUME-201..209`,
`ACP-ADDDIRS-202`) must SKIP together rather than four of them hard-FAILing a false
`NOT CONFORMANT`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeAlwaysErrorsAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            self._unknown_session(msg_id, session_id)  # keeps `ACP-RESUME-211` judging resume itself
            return
        self._error(msg_id, -32603, "Internal error: resume is not actually implemented")


def main() -> None:
    ResumeAlwaysErrorsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
