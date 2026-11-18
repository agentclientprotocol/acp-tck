#!/usr/bin/env python3
"""Non-conforming fixture: it notices that a recorded `idempotencyKey` comes with a different prompt
and answers `-32602`, as it may, but then forgets the key, so the original prompt sent again with
it inserts a second message (prompt-lifecycle.mdx:457: the key stays recorded for the first
prompt). A plain retry with the same prompt still gets the original `messageId`. Violates
`ACP-PROMPT-214` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ReusedKeyRejectedThenForgottenAgent(ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._prompt_in_flight: Any = None
        self._prompt_of_key: dict[tuple[Any, Any], Any] = {}

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._prompt_in_flight = params.get("prompt")
        super()._handle_prompt(msg_id, params)

    def _record_key(self, session_id: Any, key: Any, message_id: str) -> None:
        super()._record_key(session_id, key, message_id)
        self._prompt_of_key[(self._key_scope(session_id), key)] = self._prompt_in_flight

    def _answer_recorded_key(
        self, msg_id: Any, session_id: Any, message_id: str, params: dict[str, Any]
    ) -> None:
        scope, key = self._key_scope(session_id), params.get("idempotencyKey")
        if self._prompt_of_key.get((scope, key)) != params.get("prompt"):
            self._recorded_keys.get(scope, {}).pop(key, None)
            self._error(msg_id, -32602, "Invalid params: idempotencyKey was used with a different prompt")
            return
        super()._answer_recorded_key(msg_id, session_id, message_id, params)


def main() -> None:
    ReusedKeyRejectedThenForgottenAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-reused-key-rejected-then-forgotten"
    ).run()


if __name__ == "__main__":
    main()
