#!/usr/bin/env python3
"""Conforming fixture: `asks_permission.py`, but every permission request offers a single
`reject_always` option. The TCK's default `allow` policy must not select a `*_always` it was
not asked for (it would store a standing deny in a real agent): it sends `session/cancel` and
answers `cancelled` instead (`docs/protocol/v1/draft/prompt-turn.mdx:641`), so every prompt
turn ends `cancelled`. ACP-PERM-001 SKIPs (no `reject_once`); nothing FAILs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from asks_permission import AsksPermissionAgent  # noqa: E402


class PermOnlyRejectAlwaysAgent(AsksPermissionAgent):
    def _permission_options(self) -> list[dict[str, Any]]:
        return [{"optionId": "reject-always", "name": "Never", "kind": "reject_always"}]


def main() -> None:
    PermOnlyRejectAlwaysAgent(agent_name="tck-fixture-perm-only-reject-always").run()


if __name__ == "__main__":
    main()
