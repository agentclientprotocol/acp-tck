#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` never sends a `session_info_update` before
responding (session-setup.mdx:358-361). Replay and the state snapshot are correct.

FAILs exactly `ACP-RESUME-214` (ADVISORY).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeNoSessionInfoAgent(ConformingAgent):
    def _send_resume_session_info(self, session_id: Any) -> None:
        pass


def main() -> None:
    ResumeNoSessionInfoAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
