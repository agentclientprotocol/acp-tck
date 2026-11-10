#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive` without
`sessionCapabilities.list`. Violates ACP-ARCHIVE-001 only; the archive tests that also need
`list` SKIP, and ACP-ARCHIVE-005 (which needs only archive/unarchive) still PASSes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"archive": {}}}


def main() -> None:
    ConformingAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-archive-without-list").run()


if __name__ == "__main__":
    main()
