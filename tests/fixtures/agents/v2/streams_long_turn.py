#!/usr/bin/env python3
"""Conforming fixture: a turn that streams `agent_message_chunk`s for about 4 s before it ends
and advertises nothing cancellable, like a real agent writing a long answer. The CLI tests run
it with `--timeout 1`, so the turn outlasts the per-response timeout. `ACP-TOOLCANCEL-*` and
`ACP-TERMCANCEL-*` have nothing to judge and all SKIP; the TCK must not report its own overall
deadline as the agent's failure. Within the `-k` scope of the `test_item_controls.py` module.
"""

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

_CHUNKS = 16
_PAUSE = 0.25


class StreamsLongTurnAgent(ConformingAgent):
    def _finish_turn(self, session_id: Any, stop_reason: str | None = None) -> None:
        self._message_count += 1
        message_id = f"msg-stream-{self._message_count:04d}"
        for _ in range(_CHUNKS):
            self._send_update(
                session_id,
                {
                    "sessionUpdate": "agent_message_chunk",
                    "messageId": message_id,
                    "content": {"type": "text", "text": "word "},
                },
            )
            time.sleep(_PAUSE)
        super()._finish_turn(session_id, stop_reason)


def main() -> None:
    StreamsLongTurnAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
