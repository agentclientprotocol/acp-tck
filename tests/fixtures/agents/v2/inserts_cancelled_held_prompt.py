#!/usr/bin/env python3
"""Non-conforming fixture, for `--cancel-prompt __hang__`: `session/cancel` answers the prompt
held during a `__hang__` turn `-32800` as it should, but then inserts it anyway (a user message
under a new `messageId`, then a normal turn). A held prompt covered by the cancel is never
inserted: FAILs exactly `ACP-CANCEL-214`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class InsertsCancelledHeldPromptAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        if message.get("method") != "session/cancel" or "id" in message:
            super()._handle(message)
            return
        session_id = (message.get("params") or {}).get("sessionId")
        held = list(self._held_prompts.get(session_id, []))
        super()._handle(message)  # answers them -32800, then ends the hanging turn `cancelled`
        for _, params in held:
            self._message_count += 1
            message_id = f"msg-{self._message_count:04d}"
            self._send_user_message_update(session_id, message_id, params.get("prompt") or [])
            self._send_running_update(session_id)
            self._finish_turn(session_id)


def main() -> None:
    InsertsCancelledHeldPromptAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
