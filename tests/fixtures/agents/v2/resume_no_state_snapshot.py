#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` never sends the current-state `state_update`
snapshot before responding. Replay itself is correct.

FAILs exactly `ACP-RESUME-206`. Every other `ACP-RESUME-*` row is unaffected: none of them
needs the snapshot.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeNoStateSnapshotAgent(ConformingAgent):
    def _send_resume_snapshot(self, session_id: Any) -> None:
        pass


def main() -> None:
    ResumeNoStateSnapshotAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
