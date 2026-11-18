#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options`; `session/new` lists its
commands correctly but `session/options` lists two commands with the same `name`. Violates
ACP-COMMANDS-201 only (through the `session/options` result).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES  # noqa: E402

COMMANDS = [{"type": "command", "name": "tck", "description": "A TCK command"}]


class OptionsDuplicateCommandsAgent(ConformingAgent):
    def _options_result(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"availableCommands": [*COMMANDS, *COMMANDS]}


def main() -> None:
    OptionsDuplicateCommandsAgent(
        capabilities=CAPABILITIES,
        available_commands=COMMANDS,
        agent_name="tck-fixture-options-duplicate-commands",
    ).run()


if __name__ == "__main__":
    main()
