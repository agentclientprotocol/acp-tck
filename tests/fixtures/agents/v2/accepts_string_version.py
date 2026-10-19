#!/usr/bin/env python3
"""Non-conforming fixture: coerces a string `protocolVersion` such as `"2"` to an integer and
selects it, instead of rejecting the non-integer value with `-32602` (initialization.mdx:117) --
the same coercion the Python SDK applies. FAILs exactly `ACP-INIT-206`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsStringVersionAgent(ConformingAgent):
    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        requested = params.get("protocolVersion")
        if isinstance(requested, str) and requested.isdigit():
            params = {**params, "protocolVersion": int(requested)}
        super()._handle_initialize(msg_id, params)


def main() -> None:
    AcceptsStringVersionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
