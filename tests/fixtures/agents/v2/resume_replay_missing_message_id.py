#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` with `replayFrom: {"type": "start"}` replays history
correctly (before responding), but strips `messageId` from every replayed update -- so a
replayed `user_message` can never be matched back to the original prompt turn it came from.

FAILs exactly `ACP-RESUME-204` and `ACP-RESUME-209` (a message update without `messageId` is
schema-invalid). `ACP-RESUME-201`/`202`/`203`/`206` (resume itself, replay-before-response
ordering, the no-`replayFrom` no-replay rule, and the state snapshot) are unaffected -- none of
them inspect `messageId`. `ACP-RESUME-205` is vacuous here regardless (this fixture, like
`ConformingAgent`, never emits a `*_chunk` update).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeReplayMissingMessageIdAgent(ConformingAgent):
    def _replay_history(self, session_id: Any) -> None:
        for update in self._history.get(session_id, []):
            mangled = dict(update)
            mangled.pop("messageId", None)
            self._notify("session/update", {"sessionId": session_id, "update": mangled})


def main() -> None:
    ResumeReplayMissingMessageIdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
