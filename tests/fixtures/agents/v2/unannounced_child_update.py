#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`'s child traffic, but without ever sending the
`subagent_update` that must announce the child first. The defect is inside the turn, so it FAILs
both `ACP-PROMPT-002` (in-turn notifications) and `ACP-SUBAGENT-001` (the whole connection) and
nothing else.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class UnannouncedChildUpdateAgent(ExposesSubagentAgent):
    announce_child = False


def main() -> None:
    UnannouncedChildUpdateAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
