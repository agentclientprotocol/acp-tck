#!/usr/bin/env python3
"""Non-conforming fixture: after a failed `initialize` it refuses every later request, including a
corrected `initialize`, with `-32600` -- it will not retry (initialization.mdx:92). FAILs exactly
`ACP-INIT-211`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class NoRetryAfterFailedInitializeAgent(ConformingAgent):
    _allow_initialize_retry = False


def main() -> None:
    NoRetryAfterFailedInitializeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
