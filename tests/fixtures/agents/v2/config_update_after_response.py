#!/usr/bin/env python3
"""Non-conforming fixture: the `config_option_update` that duplicates a
`session/set_config_option` change is sent after the response instead of before it
(session-config-options.mdx:377-379, SHOULD). FAILs exactly `ACP-CONFIG-212` (ADVISORY);
`ACP-CONFIG-211` PASSes, since the update still arrives within the quiet drain.
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


class ConfigUpdateAfterResponseAgent(ConformingAgent):
    def _reply_config_set(self, msg_id: Any, session_id: Any, config_id: Any) -> None:
        options = self._config_set_options(config_id)
        self._reply(msg_id, {"configOptions": options})
        self._send_update(
            session_id, {"sessionUpdate": "config_option_update", "configOptions": options}
        )


def main() -> None:
    ConfigUpdateAfterResponseAgent(
        capabilities={"session": {}}, config_options=[dict(_VERBOSITY_OPTION)]
    ).run()

if __name__ == "__main__":
    main()
