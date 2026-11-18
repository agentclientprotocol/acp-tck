#!/usr/bin/env python3
"""Non-conforming fixture: `resume_lists_background_subagent.py`, except a resume that replays sends
the listed child's `subagent_update` at the end of the replay, before the session's
`replay_complete`, and none after it. A replayed `subagent_update` is historical and never delivers
the child's current state, so the current one must follow `replay_complete`
(session-setup.mdx:431). A resume without replay still announces the child before the snapshot.
FAILs exactly `ACP-RESUME-224` within its `-k` scope.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from resume_lists_background_subagent import ResumeListsBackgroundSubagentAgent  # noqa: E402


class ResumeBackgroundChildAnnouncedInReplayAgent(ResumeListsBackgroundSubagentAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._announced_in_replay = False

    def _replay_history(self, session_id: Any) -> None:
        super()._replay_history(session_id)
        super()._announce_resume_child(session_id, f"{session_id}-bg-child")
        self._announced_in_replay = True

    def _announce_resume_child(self, session_id: Any, child_id: str) -> None:
        if self._announced_in_replay:
            self._announced_in_replay = False
            return
        super()._announce_resume_child(session_id, child_id)


def main() -> None:
    ResumeBackgroundChildAnnouncedInReplayAgent(
        capabilities={"session": {}}, report_background_work=True, background_on_resume=True
    ).run()


if __name__ == "__main__":
    main()
