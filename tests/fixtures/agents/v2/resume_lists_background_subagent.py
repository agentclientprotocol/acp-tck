#!/usr/bin/env python3
"""Conforming fixture: `resume_lists_background_work.py`, except the unfinished background work every
`session/resume` leaves is a child session, `<id>-bg-child`, not a tool call. The snapshot lists it
as a `subagent` item, and a current `subagent_update` for it on the resumed session (with its
`running` state) precedes the snapshot, after the session's `replay_complete` when the resume
replays (session-setup.mdx:431; subagents.mdx:470). A child announced during a replay resume gets
its own `replay_complete` too, right after the announcement (session-setup.mdx:414). The positive
control for `ACP-RESUME-224`, and it PASSes `ACP-RESUME-213` and `-223` too. The `_`-hook below is
the seam the violator fixture overrides.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeListsBackgroundSubagentAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._replaying = False  # the resume in progress carries a replay cursor

    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._replaying = self._ends_replay(params.get("replayFrom"))
        super()._handle_resume_session(msg_id, params)

    def _resume_background(self, session_id: Any) -> None:
        child_id = f"{session_id}-bg-child"
        item = {"type": "subagent", "sessionId": child_id}
        listed = self._background.setdefault(session_id, [])
        if item not in listed:
            listed.append(item)
        self._announce_resume_child(session_id, child_id)

    def _announce_resume_child(self, session_id: Any, child_id: str) -> None:
        """Hook: the current `subagent_update` sent before the snapshot that lists the child."""
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "subagent_update",
                    "sessionId": child_id,
                    "title": "background helper",
                    "state": {"state": "running"},
                },
            },
        )
        if self._replaying:
            self._send_replay_complete(child_id)  # no replayed history, but announced in the request


def main() -> None:
    ResumeListsBackgroundSubagentAgent(
        capabilities={"session": {}}, report_background_work=True, background_on_resume=True
    ).run()


if __name__ == "__main__":
    main()
