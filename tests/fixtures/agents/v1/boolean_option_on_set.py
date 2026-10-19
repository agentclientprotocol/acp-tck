#!/usr/bin/env python3
"""Non-conforming fixture: hides its `type: "boolean"` config option from `session/new` for a
client without `clientCapabilities.session.configOptions.boolean`, as it must, but then leaks it
in the complete list returned by `session/set_config_option`. Violates ACP-CONFIG-003 only (it
covers every `configOptions` payload, not just `session/new`'s); ACP-CONFIG-001/002 still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CONFIG_OPTIONS = [
    {
        "id": "model",
        "name": "Model",
        "type": "select",
        "currentValue": "fast",
        "options": [{"value": "fast", "name": "Fast"}, {"value": "slow", "name": "Slow"}],
    },
    {"id": "verbose", "name": "Verbose", "type": "boolean", "currentValue": False},
]


class BooleanOptionOnSetAgent(ConformingAgent):
    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        for option in self._config_options or []:
            if option.get("id") == params.get("configId"):
                option["currentValue"] = params.get("value")
        self._reply(msg_id, {"configOptions": list(self._config_options or [])})


def main() -> None:
    BooleanOptionOnSetAgent(
        agent_name="tck-fixture-boolean-option-on-set",
        config_options=[dict(opt) for opt in CONFIG_OPTIONS],
    ).run()


if __name__ == "__main__":
    main()
