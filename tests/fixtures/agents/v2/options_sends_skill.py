#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and `session.prompt.skill`;
`session/options` lists a `skill` command to a client that never advertised
`capabilities.session.commands.skill`. Violates ACP-CLIENTCAP-203 only (through the `session/options`
result).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"options": {}, "prompt": {"skill": {}}}}


class OptionsSendsSkillAgent(ConformingAgent):
    def _options_result(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"availableCommands": [{"type": "skill", "name": "tck-skill", "description": "A TCK skill"}]}


def main() -> None:
    OptionsSendsSkillAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-options-sends-skill").run()


if __name__ == "__main__":
    main()
