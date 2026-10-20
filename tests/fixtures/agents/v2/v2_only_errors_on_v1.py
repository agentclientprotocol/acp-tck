#!/usr/bin/env python3
"""Non-conforming fixture: a v2-only agent that answers `protocolVersion: 1` with `-32602`
(Invalid params) instead of `-32022` (Unsupported protocol version). 1 is a well-formed, in-range
version, so `-32602` is reserved for malformed values (initialization.mdx:100,117) -- the same
shortcut the Python SDK's v2 endpoint takes.

FAILs exactly `ACP-INIT-202`. Every other probe (`0`, `2`, `65535`, malformed values) still goes
through the base negotiation unchanged.

Advertises `capabilities: {"session": {}}`, same as `conforming.py`, so `ACP-SESSION-001/002`
PASS (session/new is otherwise unmodified and correct) instead of SKIPping "not advertised".
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class V2OnlyErrorsOnV1Agent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "initialize" and params.get("protocolVersion") == 1:
            self._error(msg_id, -32602, "Invalid params: protocol version 1 is not supported")
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    V2OnlyErrorsOnV1Agent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
