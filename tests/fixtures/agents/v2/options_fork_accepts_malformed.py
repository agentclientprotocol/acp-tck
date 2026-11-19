#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and `fork` and, on `session/fork`
only, silently ignores initial
`configOptions` entries that do not match the schema instead of failing the request with `-32602`. Violates ACP-OPTIONS-004 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402


class OptionsForkAcceptsMalformedAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._validate_initial_config = False
        try:
            super()._handle_fork_session(msg_id, params)
        finally:
            del self._validate_initial_config


def main() -> None:
    OptionsForkAcceptsMalformedAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-accepts-malformed",
    ).run()


if __name__ == "__main__":
    main()
