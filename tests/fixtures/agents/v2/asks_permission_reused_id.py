#!/usr/bin/env python3
"""Non-conforming fixture: sends two overlapping permission requests that share one id, so the
second reuses an id still awaiting a response. A sender MUST NOT do that: FAILs exactly
`ACP-JSONRPC-202` (the reuse half). Otherwise `asks_permission_twice.py`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from asks_permission_twice import AsksPermissionTwiceAgent  # noqa: E402


class AsksPermissionReusedIdAgent(AsksPermissionTwiceAgent):
    def _second_permission_id(self) -> Any:
        return self._pending_permission["perm_id"]


def main() -> None:
    AsksPermissionReusedIdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
