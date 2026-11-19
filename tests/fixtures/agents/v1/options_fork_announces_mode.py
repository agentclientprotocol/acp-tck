#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.options` and `fork` (no `loadSession` or
`resume`) and, for a `session/fork` that carries initial `configOptions` entries, sends a
`current_mode_update` for the new session before its response. Violates ACP-OPTIONS-008 only: a
`session/new` with entries sends nothing early.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402
from _options_config import FORK_CAPABILITIES, MODES, config_options  # noqa: E402


class OptionsForkAnnouncesModeAgent(CursorsMixin, ConformingAgent):
    _forking_with_entries = False

    def _handle_fork(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._forking_with_entries = bool(params.get("configOptions"))
        try:
            super()._handle_fork(msg_id, params)
        finally:
            self._forking_with_entries = False

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        if self._forking_with_entries and "sessionId" in result:
            self._notify(
                "session/update",
                {
                    "sessionId": result["sessionId"],
                    "update": {"sessionUpdate": "current_mode_update", "currentModeId": "default"},
                },
            )
        super()._reply(msg_id, result)


def main() -> None:
    OptionsForkAnnouncesModeAgent(
        capabilities=FORK_CAPABILITIES,
        config_options=config_options(),
        modes=dict(MODES),
        agent_name="tck-fixture-options-fork-announces-mode",
    ).run()


if __name__ == "__main__":
    main()
