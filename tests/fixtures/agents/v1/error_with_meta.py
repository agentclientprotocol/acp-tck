#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: every JSON-RPC error object carries a `_meta` key,
which `Error` does not define. Trips only ACP-SCHEMA-002.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ErrorWithMetaAgent(ConformingAgent):
    def _error(self, msg_id: Any, code: int, message: str) -> None:
        self._write(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": code, "message": message, "_meta": {}},
            }
        )


def main() -> None:
    ErrorWithMetaAgent().run()


if __name__ == "__main__":
    main()
