#!/usr/bin/env python3
"""Non-conforming fixture: `session/set_config_option` changes the configuration and replies,
but never sends the `config_option_update` (session-config-options.mdx:375, SHOULD). FAILs
exactly `ACP-CONFIG-211` (ADVISORY); `ACP-CONFIG-212` SKIPs, with no update to order.
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


class ConfigSetNoUpdateNotificationAgent(ConformingAgent):
    def _reply_config_set(self, msg_id: Any, session_id: Any, config_id: Any) -> None:
        self._reply(msg_id, {"configOptions": self._config_set_options(config_id)})


def main() -> None:
    ConfigSetNoUpdateNotificationAgent(
        capabilities={"session": {}}, config_options=[dict(_VERBOSITY_OPTION)]
    ).run()

if __name__ == "__main__":
    main()
