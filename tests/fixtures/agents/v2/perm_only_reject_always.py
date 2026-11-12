#!/usr/bin/env python3
"""Conforming fixture: `asks_permission.py`, but every permission request offers a single
`reject_always` option. Offering a `reject_*` option is not required (tool-calls.mdx:340), and
the TCK's default `allow` policy must not select a `*_always` it was not asked for (it would
store a standing deny in a real agent): it sends `session/cancel` and answers `cancelled`
instead, so every permission-asking turn ends `cancelled`. FAILs nothing.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class PermOnlyRejectAlwaysAgent(AsksPermissionAgent):
    def _permission_options(self) -> list[dict[str, Any]]:
        return [{"optionId": "reject-always", "name": "Never", "kind": "reject_always"}]


def main() -> None:
    PermOnlyRejectAlwaysAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
