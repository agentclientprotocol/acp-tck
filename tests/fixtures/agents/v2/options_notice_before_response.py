#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and, for a `session/new` that
carries initial `configOptions` entries, sends a `notice` for the new session before its response
(session-config-options.mdx:584 says to send it after). Violates ACP-OPTIONS-008 only: no
`config_option_update` is sent, and a `session/new` without entries sends nothing early.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402

FELL_BACK_NOTICE = {"sessionUpdate": "notice", "severity": "info", "title": "A config value fell back"}


class OptionsNoticeBeforeResponseAgent(ConformingAgent):
    _had_entries = False

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._had_entries = bool(params.get("configOptions"))
        try:
            super()._handle_new_session(msg_id, params)
        finally:
            self._had_entries = False

    def _before_new_response(self, session_id: str) -> None:
        if self._had_entries:
            self._notify("session/update", {"sessionId": session_id, "update": dict(FELL_BACK_NOTICE)})


def main() -> None:
    OptionsNoticeBeforeResponseAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-notice-before-response",
    ).run()


if __name__ == "__main__":
    main()
