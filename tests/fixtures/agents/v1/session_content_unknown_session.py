#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), but the tool call
that reports the spawn carries a `session` content item naming a session no `subagent_update`
ever announced. No message carries that ID as traffic (a reference is not child traffic), so
`ACP-SUBAGENT-001` passes: FAILs exactly `ACP-SUBAGENT-002`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionContentUnknownSessionAgent(ExposesSubagentAgent):
    def _referenced_session(self, child_id):
        return f"{child_id}-never-announced"


def main() -> None:
    SessionContentUnknownSessionAgent(agent_name="tck-fixture-session-content-unknown-session").run()


if __name__ == "__main__":
    main()
