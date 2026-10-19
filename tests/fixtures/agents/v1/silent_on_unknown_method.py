#!/usr/bin/env python3
"""Non-conforming fixture: never replies to an unrecognized `_`-prefixed custom request.
Violates ACP-EXT-001 only. ACP-JSONRPC-004 SKIPs (no reply to judge), and ACP-ERROR-001 still
PASSes on its other sample instead of failing on the silence.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

_HARNESS_METHODS = {"_tck/env", "_tck/big"}


class SilentOnUnknownMethodAgent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method.startswith("_") and method not in _HARNESS_METHODS:
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    SilentOnUnknownMethodAgent().run()


if __name__ == "__main__":
    main()
