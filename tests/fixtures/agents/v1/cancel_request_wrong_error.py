#!/usr/bin/env python3
"""Non-conforming fixture: answers a `__hang__` prompt cancelled by `$/cancel_request` with
`-32603` (Internal error) instead of a valid result or `-32800`. Violates ACP-JSONRPC-007 only;
`session/cancel` is still handled correctly. Needs `--cancel-prompt __hang__` to exercise it.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CancelRequestWrongErrorAgent(ConformingAgent):
    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        pending = self._pending_prompt
        if method == "$/cancel_request" and pending is not None:
            if pending["id"] == params.get("requestId"):
                self._pending_prompt = None
                self._error(pending["id"], -32603, "Internal error")
                return
        super()._handle_notification(method, params)


def main() -> None:
    CancelRequestWrongErrorAgent().run()


if __name__ == "__main__":
    main()
