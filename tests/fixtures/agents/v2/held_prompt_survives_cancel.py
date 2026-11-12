#!/usr/bin/env python3
"""Non-conforming fixture, for `--cancel-prompt __hang__`: a prompt held while a `__hang__`
prompt runs is not answered by `session/cancel`. The cancel ends the hanging turn `cancelled`,
then, after a pause longer than the TCK's race window, the held prompt is inserted and run as a
normal turn. `session/cancel` covers prompts not yet inserted and MUST answer them `-32800`:
FAILs exactly `ACP-CANCEL-214`.
"""

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class HeldPromptSurvivesCancelAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        if message.get("method") != "session/cancel" or "id" in message:
            super()._handle(message)
            return
        session_id = (message.get("params") or {}).get("sessionId")
        held = self._held_prompts.pop(session_id, [])  # kept from the cancel
        super()._handle(message)  # ends the hanging turn `cancelled`
        if held:
            time.sleep(1.0)  # past the TCK's race window (its quiet_period, 0.5 s at --timeout 2)
        for msg_id, params in held:
            self._handle_prompt(msg_id, params)


def main() -> None:
    HeldPromptSurvivesCancelAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
