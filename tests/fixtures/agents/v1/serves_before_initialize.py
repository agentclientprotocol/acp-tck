#!/usr/bin/env python3
"""Non-conforming fixture: serves requests that arrive before `initialize` instead of rejecting
them with `-32600`. Violates ACP-ERROR-005 only (the TCK's own traffic always initializes first).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ServesBeforeInitializeAgent(ConformingAgent):
    _require_initialize = False


def main() -> None:
    ServesBeforeInitializeAgent(agent_name="tck-fixture-serves-before-initialize").run()


if __name__ == "__main__":
    main()
