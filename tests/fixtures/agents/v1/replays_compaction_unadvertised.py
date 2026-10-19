#!/usr/bin/env python3
"""Non-conforming fixture: advertises `loadSession` and, when replaying a session on
`session/load`, includes a `compaction_update` although the client never advertised
`clientCapabilities.session.compaction` -- the capability is required for replay as well as live
delivery. Nothing is sent live, so this proves the replay path is checked. Violates
ACP-CLIENTCAP-005 only; the ACP-LOAD-* requirements still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"loadSession": True}


class ReplaysCompactionAgent(ConformingAgent):
    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        compaction = {"sessionUpdate": "compaction_update", "compactionId": "cmp-1", "status": "completed"}
        self._notify("session/update", {"sessionId": params.get("sessionId"), "update": compaction})
        super()._handle_load(msg_id, params)


def main() -> None:
    ReplaysCompactionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-replays-compaction-unadvertised"
    ).run()


if __name__ == "__main__":
    main()
