#!/usr/bin/env python3
"""Non-conforming fixture: `finishes_background_after_idle.py`, except after the background tool
call ends (its final status is sent) the agent never re-sends the state, so the last snapshot
still lists the finished item. The Agent SHOULD re-send the state when background work ends
(prompt-lifecycle.mdx:205).

FAILs exactly `ACP-STATE-209`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundEndNotResentAgent(ConformingAgent):
    def _resend_background_state(self, session_id: Any) -> None:
        pass


def main() -> None:
    BackgroundEndNotResentAgent(
        capabilities={"session": {}}, report_background_work=True, background_outlives_turn="finish"
    ).run()


if __name__ == "__main__":
    main()
