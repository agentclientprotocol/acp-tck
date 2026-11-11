#!/usr/bin/env python3
"""Non-conforming fixture: rejects a second `initialize` with `-32600` even before any other
request, instead of handling it like the first (initialization.mdx:139) -- the behaviour of the
Python SDK. FAILs exactly `ACP-INIT-212`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsRepeatedInitializeAgent(ConformingAgent):
    _allow_repeated_initialize = False


def main() -> None:
    RejectsRepeatedInitializeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
