#!/usr/bin/env python3
"""Conforming fixture: `reports_background_work.py`, except after each turn's idle one more
background tool call starts while the session is `idle`. The agent announces it, re-sends the
state with it listed, then ends it and re-sends the state without it (prompt-lifecycle.mdx:215).
The positive control for `ACP-STATE-210`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        capabilities={"session": {}}, report_background_work=True, background_after_idle=True
    ).run()


if __name__ == "__main__":
    main()
