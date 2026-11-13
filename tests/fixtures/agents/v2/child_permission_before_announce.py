#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except the child's `session/request_permission`
is sent before the child's `subagent_update` announcement (and not again afterwards). It is a
request, not a `session/update`, so `ACP-PROMPT-002` does not judge it: FAILs exactly
`ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildPermissionBeforeAnnounceAgent(ExposesSubagentAgent):
    def _announce_child(self, session_id, child_id):
        self._send_child_permission_request(child_id)
        super()._announce_child(session_id, child_id)

    def _child_permission_step(self, child_id):
        pass  # already sent, ahead of the announcement


def main() -> None:
    ChildPermissionBeforeAnnounceAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
