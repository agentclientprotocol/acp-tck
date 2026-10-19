#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` with a well-formed but unsupported `replayFrom`
cursor type silently resumes without replay instead of rejecting it with `-32602`. Malformed
values are still rejected.

FAILs exactly `ACP-RESUME-207`. `ACP-RESUME-208` (malformed values) and every other
`ACP-RESUME-*` row are unaffected.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeIgnoresUnknownCursorAgent(ConformingAgent):
    @staticmethod
    def _replay_from_rejection(replay_from: Any) -> str | None:
        if replay_from is None:
            return None
        if not isinstance(replay_from, dict) or not isinstance(replay_from.get("type"), str):
            return "malformed replayFrom"
        return None  # any well-formed cursor accepted; only `start` actually replays


def main() -> None:
    ResumeIgnoresUnknownCursorAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
