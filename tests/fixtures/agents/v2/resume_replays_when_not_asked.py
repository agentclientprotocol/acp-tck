#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` replays the session's full retained history
unconditionally, even when `replayFrom` is omitted/`null` (which MUST NOT replay history before
responding).

FAILs exactly `ACP-RESUME-203`. `ACP-RESUME-201` (the resume itself still succeeds) and
`ACP-RESUME-202`/`204`/`205`/`206`/`209` (the replay-`{"type": "start"}` scenarios and the
state snapshot, which this fixture answers identically to `ConformingAgent`) are unaffected.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeReplaysWhenNotAskedAgent(ConformingAgent):
    @staticmethod
    def _should_replay(replay_from: Any) -> bool:
        return True


def main() -> None:
    ResumeReplaysWhenNotAskedAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
