#!/usr/bin/env python3
"""Fixture: a v1-style port that writes the `session/prompt` response only after the idle that
ends the turn. A successful response is an insertion receipt, not a completion signal: FAILs
exactly the ADVISORY `ACP-PROMPT-208`, so the verdict stays CONFORMANT.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RespondsAfterIdleAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._deferred_replies: dict[Any, tuple[Any, str]] = {}  # sessionId -> (id, messageId)

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._current_session = params.get("sessionId")
        super()._handle_prompt(msg_id, params)

    def _reply_to_prompt(self, msg_id: Any, message_id: str) -> None:
        self._deferred_replies[self._current_session] = (msg_id, message_id)

    def _send_idle_update(self, session_id: Any, stop_reason: str | None) -> None:
        super()._send_idle_update(session_id, stop_reason)
        deferred = self._deferred_replies.pop(session_id, None)
        if deferred is not None:
            self._reply(deferred[0], {"messageId": deferred[1]})


def main() -> None:
    RespondsAfterIdleAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
