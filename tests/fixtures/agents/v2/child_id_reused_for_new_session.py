#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent_full.py`, except that a `session/new` sent after a
child was announced is answered with that child's `sessionId`: a child's ID reused for an
unrelated session. The announcements themselves stay legal (the child is announced first and the
client's own session is never announced), so FAILs exactly `ACP-SUBAGENT-004` (via the later
`session/new`). Within the `-k` scope of `test_subagents`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent_full import CAPABILITIES, ExposesSubagentFullAgent  # noqa: E402


class ChildIdReusedForNewSessionAgent(ExposesSubagentFullAgent):
    def _new_session_result(self, session_id: str) -> dict[str, Any]:
        result = super()._new_session_result(session_id)
        if self._announced_children:
            result["sessionId"] = sorted(self._announced_children)[0]
        return result


def main() -> None:
    ChildIdReusedForNewSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-child-id-reused-for-new-session"
    ).run()


if __name__ == "__main__":
    main()
