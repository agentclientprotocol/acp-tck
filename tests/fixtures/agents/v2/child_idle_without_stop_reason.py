#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except the child's `idle` after its work (its own
`state_update` and the mirror on the parent) carries no `stopReason` (prompt-lifecycle.mdx:1209,
SHOULD). The prompted session's own turn-ending idle keeps its `stopReason`, so FAILs exactly
`ACP-SUBAGENT-207` (an ADVISORY row: the verdict is unchanged); `ACP-SUBAGENT-206` SKIPs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildIdleWithoutStopReasonAgent(ExposesSubagentAgent):
    _child_idle_state = {"state": "idle"}


def main() -> None:
    ChildIdleWithoutStopReasonAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
