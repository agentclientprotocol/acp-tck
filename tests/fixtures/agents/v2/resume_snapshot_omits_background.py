#!/usr/bin/env python3
"""Non-conforming fixture: `reports_background_work.py`, except the current-state snapshot of
`session/resume` leaves out `background`. Live updates carry the list, so the agent reports
background work and MUST carry the list on every `state_update`, the resume snapshot included
(session-setup.mdx:346; prompt-lifecycle.mdx:204).

FAILs exactly `ACP-RESUME-217` (`ACP-RESUME-213` SKIPs: the snapshot lists nothing).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeSnapshotOmitsBackgroundAgent(ConformingAgent):
    def _send_resume_snapshot(self, session_id: Any) -> None:
        update = {"sessionUpdate": "state_update", "state": "idle"}
        self._notify("session/update", {"sessionId": session_id, "update": update})


def main() -> None:
    ResumeSnapshotOmitsBackgroundAgent(
        capabilities={"session": {}}, report_background_work=True
    ).run()


if __name__ == "__main__":
    main()
