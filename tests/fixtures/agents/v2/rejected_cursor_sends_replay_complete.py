#!/usr/bin/env python3
"""Non-conforming fixture: rejects an unsupported or malformed `replayFrom` with `-32602` but sends
`replay_complete` first (session-setup.mdx:406: a rejected cursor replays nothing and sends no
`replay_complete`). Violates `ACP-RESUME-221` only; `ACP-RESUME-207`/`208` still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectedCursorSendsReplayCompleteAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        if self._replay_from_rejection(params.get("replayFrom")) is not None:
            self._send_replay_complete(params.get("sessionId"))
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    RejectedCursorSendsReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
