#!/usr/bin/env python3
"""Non-conforming fixture: `starts_background_after_idle.py`, except the background tool call that
starts while the session is `idle` is only announced: the agent never re-sends the state with it
listed, and the item stays live. The Agent SHOULD re-send the state when background work starts
(prompt-lifecycle.mdx:215).

FAILs exactly `ACP-STATE-210`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundStartNotResentAgent(ConformingAgent):
    def _start_background_after_idle(self, session_id: Any) -> None:
        self._tool_call_count += 1
        self._announce_background_item(session_id, f"tool-bg-{self._tool_call_count:04d}")


def main() -> None:
    BackgroundStartNotResentAgent(
        capabilities={"session": {}}, report_background_work=True, background_after_idle=True
    ).run()


if __name__ == "__main__":
    main()
