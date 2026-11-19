#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and `fork` (no `loadSession` or
`resume`) and, on `session/fork` only, accepts initial `configOptions` that name the same `configId`
twice instead of failing the request with `-32602`. Violates ACP-OPTIONS-005 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402
from _options_config import FORK_CAPABILITIES, config_options  # noqa: E402


class OptionsForkAcceptsDuplicateAgent(CursorsMixin, ConformingAgent):
    def _handle_fork(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reject_duplicate_initial_config = False
        try:
            super()._handle_fork(msg_id, params)
        finally:
            del self._reject_duplicate_initial_config


def main() -> None:
    OptionsForkAcceptsDuplicateAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-fork-accepts-duplicate",
    ).run()


if __name__ == "__main__":
    main()
