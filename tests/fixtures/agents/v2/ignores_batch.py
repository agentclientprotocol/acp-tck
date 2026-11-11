#!/usr/bin/env python3
"""Non-conforming fixture: answers `[]` with the single `-32600`/`id: null` object but silently
drops every non-empty array -- otherwise fully conforming (the shape of the Python SDK 1.0.0's
array handling). FAILs only `ACP-BATCH-209`; the connection survives (`ACP-JSONRPC-005` PASSes)
and nothing it wrote is an array (`ACP-TRANSPORT-201` PASSes), so the run stays CONFORMANT.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class IgnoresBatchAgent(ConformingAgent):
    def _handle_batch(self, items: list[Any]) -> None:
        if not items:
            super()._handle_batch(items)


def main() -> None:
    IgnoresBatchAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
