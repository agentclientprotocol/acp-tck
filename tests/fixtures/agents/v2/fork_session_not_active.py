#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.fork` and `session/fork` returns a
fresh, valid `sessionId`, but the forked session is never made active -- `session/prompt` on it
is rejected as an unknown session until it is resumed.

FAILs exactly `ACP-FORK-202`. `ACP-FORK-201` (the fork response itself) PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkSessionNotActiveAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id = params.get("sessionId")
        if source_id not in self._sessions and source_id not in self._closed_sessions:
            self._unknown_session(msg_id, source_id)
            return
        self._session_count += 1
        self._reply(msg_id, {"sessionId": f"sess-{self._session_count:04d}"})


def main() -> None:
    ForkSessionNotActiveAgent(capabilities={"session": {"fork": {}}}).run()


if __name__ == "__main__":
    main()
