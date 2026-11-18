#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options`, hides its `type: "boolean"`
config option from `session/new` as required, but `session/options` returns it to a client that
never advertised `clientCapabilities.session.configOptions.boolean`. Violates ACP-CONFIG-003 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"options": {}}}

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


class BooleanOptionOnOptionsAgent(ConformingAgent):
    def _handle_options(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"configOptions": [dict(opt) for opt in CONFIG_OPTIONS]})


def main() -> None:
    BooleanOptionOnOptionsAgent(
        capabilities=CAPABILITIES,
        agent_name="tck-fixture-boolean-option-on-options",
        config_options=[dict(opt) for opt in CONFIG_OPTIONS],
    ).run()


if __name__ == "__main__":
    main()
