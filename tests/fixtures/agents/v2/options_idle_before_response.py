#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.options` and, for a `session/new` that
carries initial `configOptions` entries, sends the optional initial idle `state_update` for the new
session before its response, as an async snapshot that overtakes a response slowed by applying
the entries would. The snapshot may arrive before or after the response (session-setup.mdx:100-103)
and is not caused by the entries, so ACP-OPTIONS-008 PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402

INITIAL_IDLE = {"sessionUpdate": "state_update", "state": "idle"}


class OptionsIdleBeforeResponseAgent(ConformingAgent):
    _had_entries = False

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._had_entries = bool(params.get("configOptions"))
        try:
            super()._handle_new_session(msg_id, params)
        finally:
            self._had_entries = False

    def _before_new_response(self, session_id: str) -> None:
        if self._had_entries:
            self._notify("session/update", {"sessionId": session_id, "update": dict(INITIAL_IDLE)})


def main() -> None:
    OptionsIdleBeforeResponseAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-idle-before-response",
    ).run()


if __name__ == "__main__":
    main()
