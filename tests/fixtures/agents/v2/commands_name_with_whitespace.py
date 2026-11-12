#!/usr/bin/env python3
"""Non-conforming fixture: advertises a typed command whose `name` contains whitespace
(slash-commands.mdx:98-100: MUST NOT). The item is schema-valid, and no other row judges the
name. FAILs exactly `ACP-COMMANDS-201`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

def main() -> None:
    ConformingAgent(
        capabilities={"session": {}},
        available_commands=[{"type": "command", "name": "web search", "description": "Search the web"}],
    ).run()

if __name__ == "__main__":
    main()
