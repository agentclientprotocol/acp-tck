#!/usr/bin/env python3
"""Fixture for the `ACP-STATE-210` false-FAIL guard: `starts_background_after_idle.py`, except the
background tool call that starts while the session is `idle` is announced and reaches a final
status before any `state_update` follows. There is no list to compare it with, so
`ACP-STATE-210` SKIPs; it must not FAIL.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundStartEndsBeforeResendAgent(ConformingAgent):
    def _start_background_after_idle(self, session_id: Any) -> None:
        self._tool_call_count += 1
        tool_call_id = f"tool-bg-{self._tool_call_count:04d}"
        self._announce_background_item(session_id, tool_call_id)
        self._finalize_background_item(session_id, tool_call_id)


def main() -> None:
    BackgroundStartEndsBeforeResendAgent(
        capabilities={"session": {}}, report_background_work=True, background_after_idle=True
    ).run()


if __name__ == "__main__":
    main()
