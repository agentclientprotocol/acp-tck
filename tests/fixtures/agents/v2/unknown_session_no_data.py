#!/usr/bin/env python3
"""Non-conforming fixture: answers an inactive session with the right code, `-32002`, but no
`data.sessionId`. The schema's `Other` error-data branch accepts that, so only the hand check in
`_helpers.assert_unknown_session_error` catches it.

FAILs `ACP-ERROR-201` and `ACP-RESUME-211`, which share that assertion.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnknownSessionNoDataAgent(ConformingAgent):
    def _unknown_session(self, msg_id: Any, session_id: Any) -> None:
        self._error(msg_id, -32002, "Resource not found")


def main() -> None:
    UnknownSessionNoDataAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
