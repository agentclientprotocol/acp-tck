#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and, for a `session/new` that
carries initial `configOptions` entries, sends a `config_option_update` for the new session before
its response. Violates ACP-OPTIONS-007 (ADVISORY) only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402


class OptionsNotifiesInitialAgent(ConformingAgent):
    _had_entries = False

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._had_entries = bool(params.get("configOptions"))
        super()._handle_new_session(msg_id, params)

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        if self._had_entries and "sessionId" in result and "configOptions" in result:
            self._notify(
                "session/update",
                {
                    "sessionId": result["sessionId"],
                    "update": {"sessionUpdate": "config_option_update", "configOptions": result["configOptions"]},
                },
            )
        super()._reply(msg_id, result)


def main() -> None:
    OptionsNotifiesInitialAgent(
        capabilities=CAPABILITIES, config_options=config_options(), agent_name="tck-fixture-options-notifies-initial"
    ).run()


if __name__ == "__main__":
    main()
