#!/usr/bin/env python3
"""Non-conforming fixture: exits as soon as it receives a `_`-prefixed custom notification or a
`$/` protocol-level notification, instead of ignoring it. Violates ACP-EXT-002 and
ACP-JSONRPC-006 (the connection must stay usable); it never replies, so ACP-JSONRPC-003 still
PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ExitsOnUnknownNotificationAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method.startswith(("_", "$/")):
            sys.exit(0)
        super()._handle_notification(method, params)


def main() -> None:
    ExitsOnUnknownNotificationAgent().run()


if __name__ == "__main__":
    main()
