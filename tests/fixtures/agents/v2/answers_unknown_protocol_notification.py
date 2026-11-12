#!/usr/bin/env python3
"""Non-conforming fixture: replies to an unrecognized `$/`-prefixed notification with a bogus
error response (`{"id": null, ...}`; a null id is legal on an error, so only the reply itself is
non-conforming). FAILs `ACP-EXT-203` (SHOULD ignore it) and nothing else under
`test_extensibility.py`. `$/cancel_request` is left alone, since the cancellation rows send it.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersUnknownProtocolNotificationAgent(ConformingAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if (
            isinstance(method, str)
            and method.startswith("$/")
            and method != "$/cancel_request"
            and "id" not in message
        ):
            self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})
            return
        super()._handle(message)


def main() -> None:
    AnswersUnknownProtocolNotificationAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
