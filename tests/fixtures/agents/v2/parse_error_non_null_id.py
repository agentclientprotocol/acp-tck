#!/usr/bin/env python3
"""Non-conforming fixture: replies to a non-JSON stdin line with `-32700` but `id: 0` instead of
`id: null` (there is no request id to echo).

FAILs exactly `ACP-ERROR-204` (ADVISORY).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ParseErrorNonNullIdAgent(ConformingAgent):
    def _handle_malformed_line(self) -> None:
        self._error(0, -32700, "Parse error")


def main() -> None:
    ParseErrorNonNullIdAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
