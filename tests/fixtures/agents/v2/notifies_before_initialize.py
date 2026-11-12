#!/usr/bin/env python3
"""Non-conforming fixture: writes a `_fixture/hello` notification at startup, before any
`initialize` has been sent -- "Agents MUST NOT send requests or notifications" while the
connection is uninitialized (initialization.mdx:91). FAILs exactly `ACP-INIT-210`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class NotifiesBeforeInitializeAgent(ConformingAgent):
    def run(self) -> None:
        self._notify("_fixture/hello", {})
        super().run()


def main() -> None:
    NotifiesBeforeInitializeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
