#!/usr/bin/env python3
"""Non-conforming fixture: advertises two commands sharing the `name` `tck`
(slash-commands.mdx:98-100: MUST be unique within the list). Both items are schema-valid. FAILs
exactly `ACP-COMMANDS-201`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

def main() -> None:
    ConformingAgent(
        capabilities={"session": {}},
        available_commands=[
            {"type": "command", "name": "tck", "description": "First"},
            {"type": "command", "name": "tck", "description": "Second"},
        ],
    ).run()

if __name__ == "__main__":
    main()
