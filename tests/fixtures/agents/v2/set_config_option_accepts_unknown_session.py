#!/usr/bin/env python3
"""Non-conforming fixture: advertises a `select` config option and applies
`session/set_config_option` to a session that does not exist, instead of `-32002` with
`data.sessionId`.

FAILs exactly `ACP-ERROR-004` (its `set_config_option` probe only runs when `session/new`
returns `configOptions`); `ACP-ERROR-003`'s `session/prompt` probes still PASS.
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
    ],
}


class SetConfigOptionAcceptsUnknownSessionAgent(ConformingAgent):
    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        config_id = params.get("configId")
        for option in self._config_options:
            if option.get("configId") == config_id:
                option["currentValue"] = params.get("value")
                self._reply(msg_id, {"configOptions": self._current_config_options()})
                return
        self._error(msg_id, -32602, "Invalid params: unknown configId")


def main() -> None:
    SetConfigOptionAcceptsUnknownSessionAgent(
        capabilities={"session": {}}, config_options=[dict(_VERBOSITY_OPTION)]
    ).run()


if __name__ == "__main__":
    main()
