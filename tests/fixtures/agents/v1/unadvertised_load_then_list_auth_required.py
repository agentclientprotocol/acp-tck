#!/usr/bin/env python3
"""Non-conforming fixture: serves `session/load` although it does not advertise `loadSession`
(instead of `-32601`), and answers the also-unadvertised `session/list` with `-32000`. The
`-32000` must not hide the `session/load` problem. Violates ACP-ERROR-006 only (ADVISORY).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnadvertisedLoadThenListAuthRequiredAgent(ConformingAgent):
    def _method_advertised(self, method: str) -> bool:
        return method in ("session/load", "session/list") or super()._method_advertised(method)

    def _handle_list(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32000, "Authentication required")


def main() -> None:
    UnadvertisedLoadThenListAuthRequiredAgent(
        agent_name="tck-fixture-unadvertised-load-then-list-auth-required"
    ).run()


if __name__ == "__main__":
    main()
