#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.options` and `fork`, but every
`session/fork` fails with `-32603`, with or without initial `configOptions` entries. FAILs
ACP-FORK-201 only: the initial-config rows leave out a fork that fails even without entries
(ACP-OPTIONS-004..006) or with the entry (ACP-OPTIONS-008), and judge `session/new`, which is
conforming.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402


class OptionsForkAlwaysFailsAgent(ConformingAgent):
    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error: forking is broken")


def main() -> None:
    OptionsForkAlwaysFailsAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-always-fails",
    ).run()


if __name__ == "__main__":
    main()
