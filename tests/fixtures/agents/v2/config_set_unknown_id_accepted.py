#!/usr/bin/env python3
"""Non-conforming fixture: `session/set_config_option` for a `configId` the session never
advertised succeeds (answering the unchanged list) instead of `-32602`
(session-config-options.mdx:234). FAILs exactly `ACP-CONFIG-207`. Invalid values are still
rejected, so `ACP-CONFIG-208` PASSes; `ACP-CONFIG-209` SKIPs (its only rejected probe needs a
second option).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

_VERBOSITY_OPTION = {
    "configId": "verbosity",
    "name": "Verbosity",
    "type": "select",
    "currentValue": "normal",
    "options": [
        {"value": "quiet", "name": "Quiet"},
        {"value": "normal", "name": "Normal"},
        {"value": "verbose", "name": "Verbose"},
    ],
}
_DEBUG_OPTION = {
    "configId": "debug_mode",
    "name": "Debug mode",
    "type": "boolean",
    "currentValue": False,
}


class ConfigSetUnknownIdAcceptedAgent(ConformingAgent):
    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        known = {option.get("configId") for option in self._config_options}
        if params.get("sessionId") in self._sessions and params.get("configId") not in known:
            self._reply(msg_id, {"configOptions": self._current_config_options()})
            return
        super()._handle_set_config_option(msg_id, params)


def main() -> None:
    ConfigSetUnknownIdAcceptedAgent(
        capabilities={"session": {}}, config_options=[dict(_VERBOSITY_OPTION)]
    ).run()

if __name__ == "__main__":
    main()
