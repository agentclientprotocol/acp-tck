#!/usr/bin/env python3
"""Non-conforming fixture: `session/set_config_option` applies the change but replies with a
`configOptions` list that omits the option it just changed. Advertises the same `select`-type
`verbosity` option as `conforming_full.py` plus a second, unrelated `boolean` option
(`debug_mode`), so the reply is still a non-empty array.

FAILs exactly `ACP-CONFIG-202`: the post-change list must contain the changed `configId`. A reply
that merely drops *other* options is not a defect -- a change may remove dependent options.
`ACP-CONFIG-201`/`203`/`204` (shape validity on `session/new`/`session/resume`, and the select
`currentValue` membership check), `ACP-CONFIG-206` and `ACP-CONFIG-211`/`212` are unaffected: the
`config_option_update` it sends before the response carries the same (partial) list.
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
    def _config_set_options(self, config_id: Any) -> list[dict[str, Any]]:
        return [dict(o) for o in self._config_options if o.get("configId") != config_id]


def main() -> None:
    ConfigSetOmitsChangedOptionAgent(
        capabilities={"session": {}},
        config_options=[dict(_VERBOSITY_OPTION), dict(_DEBUG_MODE_OPTION)],
    ).run()


if __name__ == "__main__":
    main()
