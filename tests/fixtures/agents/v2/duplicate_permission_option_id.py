#!/usr/bin/env python3
"""Non-conforming fixture: `asks_permission.py`, but its permission request offers the same
`optionId` twice (an `allow_once` and a `reject_once` option both named `allow-once`). An
`optionId` MUST be unique within the request (tool-calls.mdx:357), and the schema cannot catch
it: FAILs exactly `ACP-PERM-202`. The mock client still finds the `allow_once` option, so the
turn completes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class DuplicatePermissionOptionIdAgent(AsksPermissionAgent):
    def _permission_options(self) -> list[dict[str, Any]]:
        return [
            {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
            {"optionId": "allow-once", "name": "Reject", "kind": "reject_once"},
        ]


def main() -> None:
    DuplicatePermissionOptionIdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
