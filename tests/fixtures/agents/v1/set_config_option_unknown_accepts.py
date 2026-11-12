#!/usr/bin/env python3
"""Non-conforming fixture: advertises a select config option and accepts
`session/set_config_option` for a `configId` it never offered, or a value the option does not
offer, instead of `-32602`. Violates ACP-ERROR-007 only (it advertises no modes, so the
`session/set_mode` probe SKIPs).
"""

import sys
from pathlib import Path

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
]


class SetConfigOptionUnknownAcceptsAgent(ConformingAgent):
    _validate_set_params = False


def main() -> None:
    SetConfigOptionUnknownAcceptsAgent(
        agent_name="tck-fixture-set-config-option-unknown-accepts",
        config_options=[dict(opt) for opt in CONFIG_OPTIONS],
    ).run()


if __name__ == "__main__":
    main()
