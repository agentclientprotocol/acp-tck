#!/usr/bin/env python3
"""Non-conforming fixture, for `--cancel-prompt __hang__`: on the `__hang__` prompt it echoes
the user message and reports `running` but withholds the response; on `session/cancel` it sends
`idle(cancelled)` and then answers the already-inserted prompt with `-32800`. An inserted
message must get a successful response: FAILs exactly `ACP-PROMPT-207` (its cancelled-turn
test) and `ACP-CANCEL-203` (`-32800` after insertion). `session/close` instead answers the
prompt successfully, so `ACP-CANCEL-208` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ErrorAfterEchoAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._withhold = False
        self._withheld: dict[Any, tuple[Any, str]] = {}  # sessionId -> (id, messageId)
        self._current_session: Any = None

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._withhold = self._is_hang_prompt(params.get("prompt") or [])
        self._current_session = params.get("sessionId")
        super()._handle_prompt(msg_id, params)

    def _reply_to_prompt(self, msg_id: Any, message_id: str) -> None:
        if self._withhold:
            self._withheld[self._current_session] = (msg_id, message_id)
        else:
            super()._reply_to_prompt(msg_id, message_id)

    def _handle_cancel(self, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        super()._handle_cancel(params)
        withheld = self._withheld.pop(session_id, None)
        if withheld is not None:
            self._error(withheld[0], -32800, "Request cancelled")

    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if self._hanging_sessions.pop(session_id, None) is not None:
            self._finish_turn(session_id, "cancelled")
        withheld = self._withheld.pop(session_id, None)
        if withheld is not None:
            self._reply(withheld[0], {"messageId": withheld[1]})
        super()._handle_close_session(msg_id, params)


def main() -> None:
    ErrorAfterEchoAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
