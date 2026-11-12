#!/usr/bin/env python3
"""Conforming fixture: pushes an unsolicited `_fixture/status_update` notification right after
answering `initialize` successfully, and from then on right before handling every inbound
message (so ahead of every reply, and in the quiet period after every notification), including
ahead of the rejection of a JSON array. It never pushes while the connection is uninitialized
("Agents MUST NOT send requests or notifications", initialization.mdx:91), even after a failed
`initialize`. Otherwise identical to `ConformingAgent`; every push is a single object, never an
array (`ACP-TRANSPORT-001`).

These pushes are notifications, not replies: they must neither fail a "no reply" check
(`ACP-JSONRPC-003`, `ACP-EXT-002`) nor be mistaken for the reply a check is waiting for
(`ACP-BATCH-209`, the `ACP-INFO-*` probes' recorded behaviour).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

_STATUS = {"jsonrpc": "2.0", "method": "_fixture/status_update", "params": {"status": "ready"}}


class PushesStatusNotificationsAgent(ConformingAgent):
    def _push_status(self) -> None:
        self._write_line(_STATUS)

    def _handle(self, message: dict[str, Any]) -> None:
        if self._initialized:
            self._push_status()
        super()._handle(message)
        if message.get("method") == "initialize" and "id" in message and self._initialized:
            self._push_status()

    def _handle_batch(self, items: list[Any]) -> None:
        if self._initialized:
            self._push_status()
        super()._handle_batch(items)


def main() -> None:
    PushesStatusNotificationsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
