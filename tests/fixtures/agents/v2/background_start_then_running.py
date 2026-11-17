#!/usr/bin/env python3
"""Fixture for the `ACP-STATE-210` false-FAIL guard: `starts_background_after_idle.py`, except the
background tool call that starts while the session is `idle` is announced and then the next
`state_update` is `running`, whose list does not name it. Only an `idle` re-send is judged
(prompt-lifecycle.mdx:205), so `ACP-STATE-210` SKIPs; it must not FAIL.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundStartThenRunningAgent(ConformingAgent):
    def _start_background_after_idle(self, session_id: Any) -> None:
        self._tool_call_count += 1
        self._announce_background_item(session_id, f"tool-bg-{self._tool_call_count:04d}")
        # Not through `_send_update`: a `running` in the replayable history is its own finding
        # (`ACP-RESUME-212`).
        update = {"sessionUpdate": "state_update", "state": "running", "background": []}
        self._notify("session/update", {"sessionId": session_id, "update": update})


def main() -> None:
    BackgroundStartThenRunningAgent(
        capabilities={"session": {}}, report_background_work=True, background_after_idle=True
    ).run()


if __name__ == "__main__":
    main()
