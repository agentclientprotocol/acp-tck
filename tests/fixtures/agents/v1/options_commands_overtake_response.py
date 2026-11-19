#!/usr/bin/env python3
"""Conforming fixture: advertises `sessionCapabilities.options` and announces its (empty) command
list with an `available_commands_update` for every new session, unrelated to initial
`configOptions` entries. A plain `session/new` sends it just after its response; when the request
carries entries, applying them delays the response and the update comes first. The same request
without entries sends that kind too, so ACP-OPTIONS-008 does not attribute it to the entries and
PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import CAPABILITIES, config_options  # noqa: E402

COMMANDS = {"sessionUpdate": "available_commands_update", "availableCommands": []}


class OptionsCommandsOvertakeResponseAgent(ConformingAgent):
    _had_entries: bool | None = None

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._had_entries = bool(params.get("configOptions"))
        try:
            super()._handle_new_session(msg_id, params)
        finally:
            self._had_entries = None

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        session_id = result.get("sessionId") if self._had_entries is not None else None
        update = {"sessionId": session_id, "update": dict(COMMANDS)}
        if session_id is not None and self._had_entries:
            self._notify("session/update", update)
        super()._reply(msg_id, result)
        if session_id is not None and not self._had_entries:
            self._notify("session/update", update)


def main() -> None:
    OptionsCommandsOvertakeResponseAgent(
        capabilities=CAPABILITIES,
        config_options=config_options(),
        agent_name="tck-fixture-options-commands-overtake-response",
    ).run()


if __name__ == "__main__":
    main()
