#!/usr/bin/env python3
"""Non-conforming fixture: exits the moment it sees any batch-shaped (top-level JSON array) line
on stdin -- otherwise fully conforming. FAILs the advisory `ACP-BATCH-209` and `ACP-JSONRPC-005`
(whose tests send an array) via `AgentExited`; nothing it wrote was an array, so the MANDATORY
`ACP-TRANSPORT-201` is unaffected and the run stays CONFORMANT.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CrashesOnBatchAgent(ConformingAgent):
    def _handle_batch(self, items: list[Any]) -> None:
        sys.exit(1)


def main() -> None:
    CrashesOnBatchAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
