#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` accepts a relative `cwd` instead of rejecting it with
`-32602` (session-setup.mdx:524). FAILs exactly `ACP-SESSION-204`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsRelativeCwdAgent(ConformingAgent):
    @staticmethod
    def _cwd_rejection(cwd: Any) -> str | None:
        return None


def main() -> None:
    AcceptsRelativeCwdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
