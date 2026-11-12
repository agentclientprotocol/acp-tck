#!/usr/bin/env python3
"""Non-conforming fixture: reports background work like `reports_background_work.py`, but lists
its background tool call without a `tool_call_update` announcing it first. Items MUST be
announced before the first snapshot that lists them: FAILs exactly `ACP-STATE-207`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundUnannouncedItemAgent(ConformingAgent):
    def _announce_background_item(self, session_id: Any, tool_call_id: str) -> None:
        pass


def main() -> None:
    BackgroundUnannouncedItemAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
