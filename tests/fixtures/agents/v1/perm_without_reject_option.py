#!/usr/bin/env python3
"""Conforming fixture that offers only `allow_always` and `allow_once` permission options (no
reject option; the client can always cancel instead), and creates the probe file only after
`allow-once`. ACP-PERM-001 SKIPs (the TCK cancels rather than select an `allow_*` option);
ACP-PERM-002 PASSes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from honors_permission import HonorsPermissionAgent  # noqa: E402


class PermWithoutRejectOptionAgent(HonorsPermissionAgent):
    def _permission_options(self) -> list[dict[str, Any]]:
        return [
            {"optionId": "allow-always", "name": "Always", "kind": "allow_always"},
            {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
        ]


def main() -> None:
    PermWithoutRejectOptionAgent(agent_name="tck-fixture-perm-without-reject-option").run()


if __name__ == "__main__":
    main()
