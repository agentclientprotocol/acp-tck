#!/usr/bin/env python3
"""Non-conforming fixture: serves requests before `initialize` completes -- on a fresh connection
and after a failed `initialize` -- instead of rejecting them with `-32600` (error.mdx:60). FAILs
`ACP-INIT-209`, and `ACP-INIT-207` too: its `session/new` after `-32022` succeeds.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ServesBeforeInitializeAgent(ConformingAgent):
    _require_initialize = False


def main() -> None:
    ServesBeforeInitializeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
