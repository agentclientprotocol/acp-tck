#!/usr/bin/env python3
"""Conforming fixture, for `--cancel-prompt __hang__`: the `__hang__` prompt is held before
insertion -- no response, no user-message echo, no state change -- until `session/cancel` or
`session/close` arrives, which answers it `-32800`. With no foreground work started, no idle
is owed. Positive control for `ACP-CANCEL-203`/`ACP-CANCEL-208`/`ACP-PROMPT-207` accepting the
pre-insertion `-32800`; the verdict is CONFORMANT.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CancelBeforeInsertionAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._held: dict[Any, Any] = {}  # sessionId -> held session/prompt id

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id in self._sessions and self._is_hang_prompt(params.get("prompt") or []):
            self._held[session_id] = msg_id
            return
        super()._handle_prompt(msg_id, params)

    def _release(self, session_id: Any) -> None:
        held = self._held.pop(session_id, None)
        if held is not None:
            self._error(held, -32800, "Request cancelled")

    def _handle_cancel(self, params: dict[str, Any]) -> None:
        self._release(params.get("sessionId"))
        super()._handle_cancel(params)

    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._release(params.get("sessionId"))
        super()._handle_close_session(msg_id, params)


def main() -> None:
    CancelBeforeInsertionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
