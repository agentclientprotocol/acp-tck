#!/usr/bin/env python3
"""Non-conforming fixture: `resume_lists_background_work.py`, except the resume snapshot lists
the unfinished background tool call without first sending a `tool_call_update` for it
(session-setup.mdx:346).

FAILs exactly `ACP-RESUME-213`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeBackgroundWithoutUpdatesAgent(ConformingAgent):
    def _announce_resume_background(self, session_id: Any, tool_call_id: str) -> None:
        pass


def main() -> None:
    ResumeBackgroundWithoutUpdatesAgent(
        capabilities={"session": {}}, report_background_work=True, background_on_resume=True
    ).run()


if __name__ == "__main__":
    main()
