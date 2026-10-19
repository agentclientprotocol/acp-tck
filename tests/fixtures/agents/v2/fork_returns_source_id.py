#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.fork` but `session/fork` answers
with the *source* session's id instead of a new one.

FAILs exactly `ACP-FORK-201`. `ACP-FORK-202` SKIPs: with no new id there is no forked session
to prompt.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkReturnsSourceIdAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"sessionId": params.get("sessionId")})


def main() -> None:
    ForkReturnsSourceIdAgent(capabilities={"session": {"fork": {}}}).run()


if __name__ == "__main__":
    main()
