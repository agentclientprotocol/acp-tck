#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities.session.options`, `list` and `close`, and has two
quirks a client must tolerate. It sends `available_commands_update` for a new session shortly after
the `session/new` response, from a timer (as adapters that load commands asynchronously do), and
it persists a session lazily: the first `session/list` leaves out a closed session that a later one
shows. Neither comes from `session/options`, so ACP-OPTIONS-002 PASSes; it FAILs nothing within
`-k test_session_options`.
"""

import sys
import threading
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _options_config import config_options  # noqa: E402

CAPABILITIES = {"session": {"options": {}, "list": {}, "close": {}}}
_COMMANDS_DELAY = 0.1


class OptionsLateSetupTrafficAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._write_lock = threading.Lock()
        self._lists = 0

    def _write(self, obj: dict[str, Any]) -> None:
        with self._write_lock:
            super()._write(obj)

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        super()._reply(msg_id, result)
        session_id = result.get("sessionId")
        if isinstance(session_id, str) and session_id in self._sessions:
            update = {"sessionUpdate": "available_commands_update", "availableCommands": []}
            timer = threading.Timer(
                _COMMANDS_DELAY, self._notify, ("session/update", {"sessionId": session_id, "update": update})
            )
            timer.daemon = True
            timer.start()

    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._lists += 1
        if self._lists > 1:
            super()._handle_list_sessions(msg_id, params)
            return
        closed, self._closed_sessions = self._closed_sessions, {}
        try:
            super()._handle_list_sessions(msg_id, params)
        finally:
            self._closed_sessions = closed


def main() -> None:
    OptionsLateSetupTrafficAgent(
        capabilities=CAPABILITIES, config_options=config_options(), agent_name="tck-fixture-options-late-setup-traffic"
    ).run()


if __name__ == "__main__":
    main()
