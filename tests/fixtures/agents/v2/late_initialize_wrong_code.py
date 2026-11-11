#!/usr/bin/env python3
"""Non-conforming fixture: rejects an `initialize` repeated after another request, but with
`-32602` instead of `-32600` (error.mdx:29,60). FAILs exactly `ACP-INIT-215`; `ACP-INIT-213`
only asks for an error, so it PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class LateInitializeWrongCodeAgent(ConformingAgent):
    def _initialize_refused(self, msg_id: Any) -> bool:
        if self._initialized and self._request_seen:
            self._error(msg_id, -32602, "Invalid params: initialize already completed")
            return True
        return super()._initialize_refused(msg_id)


def main() -> None:
    LateInitializeWrongCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
