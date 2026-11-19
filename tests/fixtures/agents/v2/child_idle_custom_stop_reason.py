#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except the child's `idle` (its own `state_update` and
the mirror on the parent) carries the custom, non-underscore `stopReason` `child_done`, which the
schema's fallback branch accepts but extensions MUST NOT define (extensibility.mdx:242). The
prompted session's own turn-ending idle stays `end_turn`, so FAILs exactly `ACP-SUBAGENT-206`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildIdleCustomStopReasonAgent(ExposesSubagentAgent):
    _child_idle_state = {"state": "idle", "stopReason": "child_done"}


def main() -> None:
    ChildIdleCustomStopReasonAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
