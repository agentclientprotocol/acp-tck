#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` with `replayFrom: {"type": "start"}` replies to the
`session/resume` request *before* replaying the session's retained history, instead of after.
The current-state snapshot still precedes the response.

FAILs exactly `ACP-RESUME-202` (the replay-before-response ordering check). `ACP-RESUME-201`
and `ACP-RESUME-203` are unaffected -- this fixture only reorders the `{"type": "start"}` case.
`ACP-RESUME-204` legitimately SKIPs rather than FAILs: `_helpers.resume_session`'s
single-response-tracking read loop returns as soon as it sees the response, before ever reading
the trailing replay notifications still queued in the pipe -- so `updates` comes back empty and
ACP-RESUME-204 correctly reports the message as not replayed, rather than fabricating a false
FAIL/PASS from data it never observed. `ACP-RESUME-206`/`209` see only the snapshot before the
response, which is valid.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeRespondsBeforeReplayAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        rejection = self._replay_from_rejection(params.get("replayFrom"))
        if rejection is not None:
            self._error(msg_id, -32602, f"Invalid params: {rejection}")
            return
        session_id = params.get("sessionId")
        if session_id not in self._sessions:
            self._sessions[session_id] = params.get("cwd", "")
        self._send_resume_snapshot(session_id)
        self._reply(msg_id, self._resume_result())
        if self._should_replay(params.get("replayFrom")):
            self._replay_history(session_id)


def main() -> None:
    ResumeRespondsBeforeReplayAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
