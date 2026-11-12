#!/usr/bin/env python3
"""Non-conforming fixture: answers every `$/cancel_request` notification with an error naming
the cancelled id (`-32602`, "unknown request"). A receiver MUST ignore one for an unknown or
already-answered id and never send a second response: FAILs exactly `ACP-JSONRPC-006`,
`ACP-CANCEL-211`, and `ACP-JSONRPC-007` (the withdrawn prompt, already answered, gets this error
as a second response).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersCancelRequestAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        if message.get("method") == "$/cancel_request" and "id" not in message:
            params = message.get("params") or {}
            self._error(params.get("requestId"), -32602, "Invalid params: unknown request")
            return
        super()._handle(message)


def main() -> None:
    AnswersCancelRequestAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
