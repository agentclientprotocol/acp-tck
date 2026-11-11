#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.fork`; `session/fork` of a source it
never created answers `-32602` (invalid params) instead of `-32002` with `data.sessionId`.

FAILs exactly `ACP-FORK-203`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkUnknownSourceInvalidParamsAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id = params.get("sessionId")
        if source_id not in self._sessions and source_id not in self._closed_sessions:
            self._error(msg_id, -32602, f"Invalid params: unknown sessionId {source_id!r}")
            return
        super()._handle_fork_session(msg_id, params)


def main() -> None:
    ForkUnknownSourceInvalidParamsAgent(capabilities={"session": {"fork": {}}}).run()


if __name__ == "__main__":
    main()
