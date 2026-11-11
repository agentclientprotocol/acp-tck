#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.fork` but `session/fork` answers
with the *source* session's id instead of a new one.

FAILs `ACP-FORK-201` and `ACP-FORK-204` (which also requires a new id, forking a closed
session). `ACP-FORK-202` SKIPs: with no new id there is no forked session to prompt. An unknown
source is still answered `-32002`, so `ACP-FORK-203` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkReturnsSourceIdAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id = params.get("sessionId")
        if source_id not in self._sessions and source_id not in self._closed_sessions:
            self._unknown_session(msg_id, source_id)
            return
        self._reply(msg_id, {"sessionId": source_id})


def main() -> None:
    ForkReturnsSourceIdAgent(capabilities={"session": {"fork": {}}}).run()


if __name__ == "__main__":
    main()
