#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and `fork` and, for a
`session/fork` that carries initial `configOptions` entries, sends a `notice` for the new session
before its response (session-config-options.mdx:584 says to send it after). Violates
ACP-OPTIONS-008 only: a `session/new` with entries, and a fork without them, send nothing early.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402
from options_notice_before_response import FELL_BACK_NOTICE  # noqa: E402


class OptionsForkNoticeBeforeResponseAgent(ConformingAgent):
    _forking_with_entries = False

    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._forking_with_entries = bool(params.get("configOptions"))
        try:
            super()._handle_fork_session(msg_id, params)
        finally:
            self._forking_with_entries = False

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        if self._forking_with_entries and "sessionId" in result:
            self._notify("session/update", {"sessionId": result["sessionId"], "update": dict(FELL_BACK_NOTICE)})
        super()._reply(msg_id, result)


def main() -> None:
    OptionsForkNoticeBeforeResponseAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-notice-before-response",
    ).run()


if __name__ == "__main__":
    main()
