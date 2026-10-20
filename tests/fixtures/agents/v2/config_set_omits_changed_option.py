#!/usr/bin/env python3
"""Non-conforming fixture: `session/set_config_option` applies the change but replies with a
`configOptions` list that omits the option it just changed. Advertises the same `select`-type
`verbosity` option as `conforming_full.py` plus a second, unrelated `boolean` option
(`debug_mode`), so the reply is still a non-empty array.

FAILs exactly `ACP-CONFIG-202`: the post-change list must contain the changed `configId`. A reply
that merely drops *other* options is not a defect -- a change may remove dependent options.
`ACP-CONFIG-201`/`203`/`204` (shape validity on `session/new`/`session/resume`, and the select
`currentValue` membership check) and `ACP-CONFIG-206` (vacuous unless a `config_option_update`
is observed, which this fixture never sends) are unaffected.
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

_DEBUG_MODE_OPTION = {
    "configId": "debug_mode",
    "name": "Debug mode",
    "type": "boolean",
    "currentValue": False,
}


class ConfigSetOmitsChangedOptionAgent(ConformingAgent):
    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        config_id = params.get("configId")
        for option in self._config_options:
            if option.get("configId") == config_id:
                option["currentValue"] = params.get("value")
                others = [dict(o) for o in self._config_options if o.get("configId") != config_id]
                self._reply(msg_id, {"configOptions": others})
                return
        self._error(msg_id, -32602, "Invalid params: unknown configId")


def main() -> None:
    ConfigSetOmitsChangedOptionAgent(
        capabilities={"session": {}},
        config_options=[dict(_VERBOSITY_OPTION), dict(_DEBUG_MODE_OPTION)],
    ).run()


if __name__ == "__main__":
    main()
