#!/usr/bin/env python3
"""Non-conforming fixture: like `pushes_status_notifications.py`, but instead of rejecting a JSON
array it dispatches the elements and answers each on its own line (the replies are not an array),
with a status notification pushed between them.

Proves skipping the agent's own notifications does not hide element processing: FAILs exactly
`ACP-BATCH-209` (a reply carries an element's `id`). Nothing it writes is an array, so
`ACP-TRANSPORT-001` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from pushes_status_notifications import PushesStatusNotificationsAgent  # noqa: E402


class PushesStatusAndProcessesArrayElementsAgent(PushesStatusNotificationsAgent):
    def _handle_batch(self, items: list[Any]) -> None:
        if not items:
            super()._handle_batch(items)
            return
        for index, item in enumerate(items):
            if index:
                self._push_status()
            if isinstance(item, dict) and item.get("jsonrpc") == "2.0" and "method" in item:
                self._handle(item)
            else:
                self._write(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
                )


def main() -> None:
    PushesStatusAndProcessesArrayElementsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
