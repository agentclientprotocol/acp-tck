#!/usr/bin/env python3
"""Conforming fixture that reports background work: `conforming.py` plus
`report_background_work=True` (see `_base.ConformingAgent._run_background_work`). Every
`state_update` carries a `background` list, and each turn lists one background tool call after
announcing it and finalizes it before the turn-ending idle removes it. The positive control for
`ACP-STATE-206..208`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
