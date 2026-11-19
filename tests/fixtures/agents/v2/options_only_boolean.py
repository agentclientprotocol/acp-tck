#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.options` with a single boolean option, and
ignores an initial `configOptions` entry whose `configId` is unknown before it looks for duplicates
(for an unknown id the duplicate rule and the rule to ignore it both apply). ACP-OPTIONS-005
duplicates the real boolean option, which this agent rejects with `-32602`, so it PASSes; it FAILs
nothing within `-k test_initial_config`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES  # noqa: E402


class OptionsOnlyBooleanAgent(ConformingAgent):
    _reject_duplicate_initial_config = False

    def _initial_config_error(self, entries: Any) -> str | None:
        error = super()._initial_config_error(entries)
        if error is not None:
            return error
        known = {o.get("configId") for o in self._config_options}
        seen: set[str] = set()
        for entry in entries or []:
            config_id = entry["configId"]
            if config_id in known and config_id in seen:
                return f"configOptions names {config_id!r} twice"
            seen.add(config_id)
        return None


def main() -> None:
    OptionsOnlyBooleanAgent(
        capabilities=CAPABILITIES,
        config_options=[{"configId": "verbose", "name": "Verbose", "type": "boolean", "currentValue": False}],
        agent_name="tck-fixture-options-only-boolean",
    ).run()


if __name__ == "__main__":
    main()
