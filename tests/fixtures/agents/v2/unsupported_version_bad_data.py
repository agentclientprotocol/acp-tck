#!/usr/bin/env python3
"""Non-conforming fixture: rejects unsupported versions with the right `-32022` code, but its
`data` omits the required `supported` array (initialization.mdx:100). FAILs exactly
`ACP-INIT-205`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnsupportedVersionBadDataAgent(ConformingAgent):
    def _reject_unsupported_version(self, msg_id: Any, requested: int) -> None:
        self._init_rejected = True
        self._write(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32022,
                    "message": "Unsupported protocol version",
                    "data": {"requested": requested},
                },
            }
        )


def main() -> None:
    UnsupportedVersionBadDataAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
