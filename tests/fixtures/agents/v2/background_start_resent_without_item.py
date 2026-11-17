#!/usr/bin/env python3
"""Non-conforming fixture: `starts_background_after_idle.py`, except the background tool call that
starts while the session is `idle` is announced and the state is re-sent as `idle`, but its
background list omits the item, which stays live. The Agent SHOULD re-send the state with the
updated list when background work starts (prompt-lifecycle.mdx:205).

FAILs exactly `ACP-STATE-210`, by the "next `idle` omits it" branch.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundStartResentWithoutItemAgent(ConformingAgent):
    def _start_background_after_idle(self, session_id: Any) -> None:
        self._tool_call_count += 1
        self._announce_background_item(session_id, f"tool-bg-{self._tool_call_count:04d}")
        self._resend_background_state(session_id)


def main() -> None:
    BackgroundStartResentWithoutItemAgent(
        capabilities={"session": {}}, report_background_work=True, background_after_idle=True
    ).run()


if __name__ == "__main__":
    main()
