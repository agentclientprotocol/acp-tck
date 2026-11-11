#!/usr/bin/env python3
"""Non-conforming fixture: sends a `config_option_update` before the `session/new` response,
although the response carries the same `configOptions` too (session-setup.mdx:103). FAILs
exactly `ACP-SESSION-207` (ADVISORY); `ACP-SESSION-208` PASSes since the response has the list.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ConfigNotifiedBeforeNewResponseAgent(ConformingAgent):
    def _before_new_response(self, session_id: str) -> None:
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "config_option_update",
                    "configOptions": self._current_config_options(),
                },
            },
        )


def main() -> None:
    ConfigNotifiedBeforeNewResponseAgent(
        capabilities={"session": {}},
        config_options=[
            {
                "configId": "verbosity",
                "name": "Verbosity",
                "type": "select",
                "currentValue": "normal",
                "options": [
                    {"value": "quiet", "name": "Quiet"},
                    {"value": "normal", "name": "Normal"},
                ],
            }
        ],
    ).run()


if __name__ == "__main__":
    main()
