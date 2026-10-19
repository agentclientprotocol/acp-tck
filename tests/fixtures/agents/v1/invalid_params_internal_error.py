#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: answers a `session/new` without `cwd` with `-32603`
(Internal error) instead of `-32602` (Invalid params). Trips only ACP-ERROR-002.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class InvalidParamsInternalErrorAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not isinstance(params.get("cwd"), str):
            self._error(msg_id, -32603, "Internal error")
            return
        super()._handle_new_session(msg_id, params)


def main() -> None:
    InvalidParamsInternalErrorAgent().run()


if __name__ == "__main__":
    main()
