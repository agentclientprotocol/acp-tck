#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and `fork` (no `loadSession` or
`resume`), but every `session/fork` fails with `-32603`, with or without initial `configOptions`
entries. The initial-config rows leave out a fork that fails even without entries
(ACP-OPTIONS-004..006) or with the entry (ACP-OPTIONS-008) and judge `session/new`, which is
conforming, so none of them FAILs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402


class OptionsForkAlwaysFailsAgent(CursorsMixin, ConformingAgent):
    def _handle_fork(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error: forking is broken")


def main() -> None:
    OptionsForkAlwaysFailsAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-always-fails",
    ).run()


if __name__ == "__main__":
    main()
