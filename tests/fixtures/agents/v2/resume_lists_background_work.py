#!/usr/bin/env python3
"""Conforming fixture: `reports_background_work.py` plus `background_on_resume=True`, so every
`session/resume` leaves the session with one unfinished background tool call. The snapshot lists
it and a `tool_call_update` announces it first (session-setup.mdx:346). The positive control for
`ACP-RESUME-213`, which SKIPs when a snapshot lists no background work.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        capabilities={"session": {}}, report_background_work=True, background_on_resume=True
    ).run()


if __name__ == "__main__":
    main()
