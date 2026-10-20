#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` treats a malformed `replayFrom` (not an object, or
an object without a string `type`) as if it were omitted, instead of rejecting it with
`-32602`. Well-formed unsupported cursor types are still rejected.

FAILs exactly `ACP-RESUME-208`. `ACP-RESUME-207` (unsupported cursor types) and every other
`ACP-RESUME-*` row are unaffected.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeAcceptsMalformedCursorAgent(ConformingAgent):
    @staticmethod
    def _replay_from_rejection(replay_from: Any) -> str | None:
        if not isinstance(replay_from, dict) or not isinstance(replay_from.get("type"), str):
            return None  # malformed: silently treated as omitted
        if replay_from["type"] != "start":
            return f"unsupported replayFrom cursor type {replay_from['type']!r}"
        return None


def main() -> None:
    ResumeAcceptsMalformedCursorAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
