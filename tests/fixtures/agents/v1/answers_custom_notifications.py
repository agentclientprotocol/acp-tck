#!/usr/bin/env python3
"""Non-conforming fixture: replies `-32601` (with `id: null`) to every `_`-prefixed custom
notification instead of ignoring it. Violates ACP-JSONRPC-003 only -- notifications never
receive a response; the connection itself stays usable (ACP-EXT-002 still PASSes).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersCustomNotificationsAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method.startswith("_"):
            self._error(None, -32601, "Method not found")
            return
        super()._handle_notification(method, params)


def main() -> None:
    AnswersCustomNotificationsAgent().run()


if __name__ == "__main__":
    main()
