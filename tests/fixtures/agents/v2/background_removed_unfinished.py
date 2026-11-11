#!/usr/bin/env python3
"""Non-conforming fixture: reports background work like `reports_background_work.py`, but its
turn-ending idle drops the background tool call from the list while the call is still
`in_progress`. A tool call's final status MUST be sent before the snapshot that removes it:
FAILs exactly `ACP-STATE-208`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundRemovedUnfinishedAgent(ConformingAgent):
    def _finalize_background_item(self, session_id: Any, tool_call_id: str) -> None:
        pass


def main() -> None:
    BackgroundRemovedUnfinishedAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
