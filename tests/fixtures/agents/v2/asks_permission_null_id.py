#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission mid-turn, but with `id: null` on the request.
A request id MUST be a string or an integer, never `null`: FAILs `ACP-JSONRPC-202` and
`ACP-PERM-201` (the request no longer validates against the schema). Otherwise conforming.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class AsksPermissionNullIdAgent(AsksPermissionAgent):
    def _next_permission_id(self) -> Any:
        return None


def main() -> None:
    AsksPermissionNullIdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
