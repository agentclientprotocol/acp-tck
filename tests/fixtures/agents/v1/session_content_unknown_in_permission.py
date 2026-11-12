#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), but the spawn's
`session/request_permission` carries a `session` content item, in its `toolCall`, naming a session
no `subagent_update` ever announced. Every other `session` reference is legitimate and no message
carries the ID as traffic, so `ACP-SUBAGENT-001` passes: FAILs exactly `ACP-SUBAGENT-002`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionContentUnknownInPermissionAgent(ExposesSubagentAgent):
    def _permission_referenced_session(self, child_id):
        return f"{child_id}-never-announced"


def main() -> None:
    SessionContentUnknownInPermissionAgent(agent_name="tck-fixture-session-content-unknown-in-permission").run()


if __name__ == "__main__":
    main()
