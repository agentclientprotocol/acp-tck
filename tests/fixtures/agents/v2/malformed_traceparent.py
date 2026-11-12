#!/usr/bin/env python3
"""Non-conforming fixture: a `session/update` notification carries
`_meta: {"traceparent": "not-a-trace-id"}`, which is not W3C Trace Context format
(`extensibility.mdx:97-100`). FAILs `ACP-META-203` only; the key is a reserved W3C one, so
`ACP-META-204` PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class MalformedTraceparentAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {"sessionUpdate": "_tck_custom_update"},
                "_meta": {"traceparent": "not-a-trace-id"},
            },
        )
        return False  # fire-and-forget: finish the turn immediately, in the same call


def main() -> None:
    MalformedTraceparentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
