#!/usr/bin/env python3
"""Non-conforming fixture: `session/list` accepts a relative `cwd` filter instead of rejecting it
with `-32602`; it simply matches no session.

FAILs exactly `ACP-LIST-205`. Every other `session/list` row sends an absolute filter, or none.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ListAcceptsRelativeCwdAgent(ConformingAgent):
    @staticmethod
    def _list_cwd_rejection(cwd: Any) -> str | None:
        return None


def main() -> None:
    ListAcceptsRelativeCwdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
