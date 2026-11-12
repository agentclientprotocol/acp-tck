#!/usr/bin/env python3
"""Non-conforming fixture: like `pushes_status_notifications.py`, but after pushing its status
notification it also replies to every notification it receives with a bogus error
response (`{"id": null, "error": ...}`).

Proves a leading agent notification does not hide a later reply: FAILs exactly
`ACP-JSONRPC-003`, `ACP-EXT-002` and `ACP-EXT-203`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from pushes_status_notifications import PushesStatusNotificationsAgent  # noqa: E402


class PushesStatusAndAnswersNotificationsAgent(PushesStatusNotificationsAgent):
    def _handle(self, message: dict[str, Any]) -> None:
        super()._handle(message)
        if "method" in message and "id" not in message:
            self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})


def main() -> None:
    PushesStatusAndAnswersNotificationsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
