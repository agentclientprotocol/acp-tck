#!/usr/bin/env python3
"""Non-conforming fixture: asks permission for the probe operation but creates the file whatever
the client answered. Violates ACP-PERM-001 and ACP-PERM-002 (both ADVISORY).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from honors_permission import HonorsPermissionAgent  # noqa: E402


class IgnoresRejectAgent(HonorsPermissionAgent):
    def _should_run(self, outcome: dict[str, Any]) -> bool:
        return True


def main() -> None:
    IgnoresRejectAgent(agent_name="tck-fixture-perm-ignores-reject").run()


if __name__ == "__main__":
    main()
