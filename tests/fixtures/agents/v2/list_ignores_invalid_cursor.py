#!/usr/bin/env python3
"""Non-conforming fixture: `session/list` ignores a `cursor` it never issued and returns the first
page instead of rejecting it with `-32602`.

FAILs exactly `ACP-LIST-206`. No other row sends a cursor: this agent never issues a
`nextCursor` for the TCK to forward.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ListIgnoresInvalidCursorAgent(ConformingAgent):
    @staticmethod
    def _list_cursor_rejection(cursor: Any) -> str | None:
        return None


def main() -> None:
    ListIgnoresInvalidCursorAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
