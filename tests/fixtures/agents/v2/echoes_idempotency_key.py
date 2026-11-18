#!/usr/bin/env python3
"""Non-conforming fixture: the `session_info_update` that a resume sends carries the session's
`idempotencyKey` in its title (prompt-lifecycle.mdx:459). Keys are otherwise handled correctly.
FAILs `ACP-PROMPT-216` (ADVISORY) only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class EchoesIdempotencyKeyAgent(ConformingAgent):
    def _send_resume_session_info(self, session_id: Any) -> None:
        keys = list(self._recorded_keys.get(session_id, {}))
        title = f"TCK fixture session {keys[0]}" if keys else "TCK fixture session"
        self._notify(
            "session/update",
            {"sessionId": session_id, "update": {"sessionUpdate": "session_info_update", "title": title}},
        )


def main() -> None:
    EchoesIdempotencyKeyAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-echoes-idempotency-key"
    ).run()


if __name__ == "__main__":
    main()
