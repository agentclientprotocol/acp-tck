#!/usr/bin/env python3
"""Conforming fixture: an agent that processes `session/close` before a `session/prompt` sent just
ahead of it. Only a prompt that is the single text `__close_first__` (pass it as
`--cancel-prompt`) is deferred, and once the close has taken effect it is answered `-32002`
(the session is no longer active, session-setup.mdx:51). `ACP-CLOSE-204` PASSes with outcome
`not_active`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ClosesBeforePromptAgent(ConformingAgent):
    _SENTINEL = "__close_first__"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._deferred_prompts: dict[Any, list[Any]] = {}

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        prompt = params.get("prompt")
        if isinstance(prompt, list) and any(
            isinstance(block, dict) and block.get("text") == self._SENTINEL for block in prompt
        ):
            self._deferred_prompts.setdefault(params.get("sessionId"), []).append(msg_id)
            return
        super()._handle_prompt(msg_id, params)

    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_close_session(msg_id, params)
        session_id = params.get("sessionId")
        for prompt_id in self._deferred_prompts.pop(session_id, []):
            self._unknown_session(prompt_id, session_id)


def main() -> None:
    ClosesBeforePromptAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
