#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options`, and `session/options` with the
`sessionId` of a closed session resumes it (the session is active again, so a prompt for it is
accepted). It otherwise answers like a conforming agent. Violates ACP-OPTIONS-002 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES  # noqa: E402


class OptionsResumesSessionAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id in self._closed_sessions:
            self._sessions[session_id] = self._closed_sessions.pop(session_id)
        super()._handle_options(msg_id, params)


def main() -> None:
    OptionsResumesSessionAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-options-resumes-session"
    ).run()


if __name__ == "__main__":
    main()
