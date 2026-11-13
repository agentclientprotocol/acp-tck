#!/usr/bin/env python3
"""Conforming fixture: `reports_background_work.py`, except each turn's background tool call is
still listed on the turn-ending idle and ends after it. The agent sends its final status, then
re-sends the idle snapshot with the item removed (prompt-lifecycle.mdx:205-206). The positive
control for `ACP-STATE-209`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        capabilities={"session": {}}, report_background_work=True, background_outlives_turn="finish"
    ).run()


if __name__ == "__main__":
    main()
