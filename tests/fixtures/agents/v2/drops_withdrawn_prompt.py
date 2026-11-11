#!/usr/bin/env python3
"""Non-conforming fixture, for `--cancel-prompt __hang__`: `cancel_before_insertion.py`, but a
`$/cancel_request` naming the held `__hang__` prompt silently discards it -- no response, ever,
not even after `session/cancel`. The receiver MUST still send a response for the original
request: FAILs exactly `ACP-CANCEL-212`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from cancel_before_insertion import CancelBeforeInsertionAgent  # noqa: E402


class DropsWithdrawnPromptAgent(CancelBeforeInsertionAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        if message.get("method") == "$/cancel_request" and "id" not in message:
            request_id = (message.get("params") or {}).get("requestId")
            for session_id, held in list(self._held.items()):
                if held == request_id:
                    del self._held[session_id]  # dropped without a response
            return
        super()._handle(message)


def main() -> None:
    DropsWithdrawnPromptAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
