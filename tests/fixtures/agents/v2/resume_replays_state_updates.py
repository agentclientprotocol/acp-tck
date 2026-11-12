#!/usr/bin/env python3
"""Non-conforming fixture: records every `state_update` into the session history and replays it
on `session/resume`, so a replayed historical `running` precedes the current-state snapshot
(session-setup.mdx:227,348). The snapshot itself is correct.

FAILs exactly `ACP-RESUME-212`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeReplaysStateUpdatesAgent(ConformingAgent):
    def _record_history(self, session_id: Any, update: dict[str, Any]) -> None:
        super()._record_history(session_id, update)
        if update.get("sessionUpdate") == "state_update":
            self._history.setdefault(session_id, []).append(dict(update))


def main() -> None:
    ResumeReplaysStateUpdatesAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
