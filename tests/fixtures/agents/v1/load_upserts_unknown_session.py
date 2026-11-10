#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: advertises `loadSession` and `resume`, but
`session/load` and `session/resume` of a session that does not exist silently create it and
succeed instead of answering `-32002` with `data.sessionId`. Trips only ACP-ERROR-004.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"resume": {}}}


class LoadUpsertsUnknownSessionAgent(ConformingAgent):
    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._sessions.setdefault(params.get("sessionId"), {"cwd": params.get("cwd"), "history": []})
        super()._handle_load(msg_id, params)

    def _handle_resume(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._sessions.setdefault(params.get("sessionId"), {"cwd": params.get("cwd"), "history": []})
        super()._handle_resume(msg_id, params)


def main() -> None:
    LoadUpsertsUnknownSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-load-upserts-unknown-session"
    ).run()


if __name__ == "__main__":
    main()
