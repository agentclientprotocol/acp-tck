#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), except the child's own
`state_update`s (`running`, `idle`) are never mirrored on the parent's `subagent_update.state`. The
announcement and everything else stay legal and schema-valid, so FAILs exactly `ACP-SUBAGENT-010`
(an ADVISORY row: the verdict is unchanged).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class UnmirroredChildStateAgent(ExposesSubagentAgent):
    _mirrors_child_state = False


def main() -> None:
    UnmirroredChildStateAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
