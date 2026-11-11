#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.fork`, but `session/fork` only accepts a
source that is active on the connection; a closed (still listed) source is answered `-32002`,
though the source only has to exist.

FAILs exactly `ACP-FORK-204`. `ACP-FORK-201`/`202`/`203` fork live sessions or an unknown id and
PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkRequiresActiveSourceAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id = params.get("sessionId")
        if source_id not in self._sessions:
            self._unknown_session(msg_id, source_id)
            return
        super()._handle_fork_session(msg_id, params)


def main() -> None:
    ForkRequiresActiveSourceAgent(capabilities={"session": {"fork": {}}}).run()


if __name__ == "__main__":
    main()
