#!/usr/bin/env python3
"""Non-conforming fixture: an invalid `session/set_config_option` value (undeclared select
value, mismatched or unsupported value `type`) is rejected with `-32603` instead of `-32602`
(session-config-options.mdx:234), leaving the configuration untouched. FAILs exactly
`ACP-CONFIG-208`; an unknown `configId` still gets `-32602`, so `ACP-CONFIG-207` PASSes.
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


class ConfigSetInvalidValueWrongCodeAgent(ConformingAgent):
    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        option = next(
            (o for o in self._config_options if o.get("configId") == params.get("configId")), None
        )
        if (
            params.get("sessionId") in self._sessions
            and option is not None
            and not self._config_value_is_valid(option, params.get("type"), params.get("value"))
        ):
            self._error(msg_id, -32603, "Internal error: invalid value")
            return
        super()._handle_set_config_option(msg_id, params)


def main() -> None:
    ConfigSetInvalidValueWrongCodeAgent(
        capabilities={"session": {}}, config_options=[dict(_VERBOSITY_OPTION)]
    ).run()

if __name__ == "__main__":
    main()
