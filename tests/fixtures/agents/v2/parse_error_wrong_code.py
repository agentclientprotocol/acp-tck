#!/usr/bin/env python3
"""Non-conforming fixture: replies to a non-JSON stdin line with `-32600` (and `id: null`)
instead of `-32700`.

FAILs exactly `ACP-ERROR-204` (ADVISORY). `ACP-INFO-PARSE-001` only records the reply.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ParseErrorWrongCodeAgent(ConformingAgent):
    def _handle_malformed_line(self) -> None:
        self._error(None, -32600, "Invalid Request")


def main() -> None:
    ParseErrorWrongCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
