#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.fork`; `session/new` carries both
`configOptions` and `availableCommands`, but the `session/fork` response leaves out
`availableCommands` (session-setup.mdx:108).

FAILs exactly `ACP-FORK-205`. `ACP-FORK-201`/`202` PASS: the omitted list is optional in the schema.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForkOmitsAvailableCommandsAgent(ConformingAgent):
    def _fork_state_fields(self) -> dict[str, Any]:
        fields = super()._fork_state_fields()
        fields.pop("availableCommands", None)
        return fields


def main() -> None:
    ForkOmitsAvailableCommandsAgent(
        capabilities={"session": {"fork": {}}},
        config_options=[
            {
                "configId": "verbosity",
                "name": "Verbosity",
                "type": "select",
                "currentValue": "normal",
                "options": [{"value": "quiet", "name": "Quiet"}, {"value": "normal", "name": "Normal"}],
            }
        ],
        available_commands=[{"type": "command", "name": "tck", "description": "A TCK command"}],
    ).run()


if __name__ == "__main__":
    main()
