#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), plus a
`subagent_update` sent on the child that announces the session the client created with
`session/new` as the child's own child: an ordinary session's ID reused for a subagent (and a
cycle). Nothing is unannounced and the update is schema-valid, so `ACP-PROMPT-002` and
`ACP-SUBAGENT-001` pass: FAILs exactly `ACP-SUBAGENT-004`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SubagentReusesSessionIdAgent(ExposesSubagentAgent):
    def _announce_nested_child(self, child_id):
        super()._announce_nested_child(child_id)
        client_session = child_id.rsplit("-child-", 1)[0]
        self._send_update(child_id, {"sessionUpdate": "subagent_update", "sessionId": client_session})


def main() -> None:
    SubagentReusesSessionIdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
