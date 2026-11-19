#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except `session/close` responds without
withdrawing the child's still-unanswered permission requests. Before it responds the Agent MUST
cancel the pending permission requests of the closed session's descendants with
`$/cancel_request` (subagents.mdx:427). FAILs exactly `ACP-SUBAGENT-203`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class CloseKeepsChildPermissionOpenAgent(ExposesSubagentAgent):
    def _withdraw_child_requests_on_close(self, session_id: Any) -> None:
        pass


def main() -> None:
    CloseKeepsChildPermissionOpenAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
