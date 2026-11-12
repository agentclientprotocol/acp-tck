#!/usr/bin/env python3
"""Non-conforming fixture: rejects a `session/new` without `cwd` with the implementation-defined
code `-32050`, inside the `-32768..-32000` range reserved for JSON-RPC and ACP (the codes
defined there are JSON-RPC's `-32700` and `-32600..-32603` and ACP's `-32000`, `-32002` and
`-32022`).

FAILs exactly `ACP-ERROR-008` (ADVISORY). The unknown-method and unknown-session replies stay
conforming, so no other row is affected.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ReservedRangeCustomCodeAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        if "cwd" not in params:
            self._error(msg_id, -32050, "cwd is required")
            return
        super()._handle_new_session(msg_id, params)


def main() -> None:
    ReservedRangeCustomCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
