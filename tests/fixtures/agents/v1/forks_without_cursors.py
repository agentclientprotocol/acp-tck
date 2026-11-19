#!/usr/bin/env python3
"""Conforming fixture: advertises `fork` and `loadSession` but never announces a cursor, and
`session/fork` rejects any `cursorId` with `-32602` since none was issued. ACP-CURSOR-003 probes
it all the same (literal reading of the rule) and PASSes; ACP-CURSOR-004 SKIPs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"fork": {}}}


class ForksWithoutCursorsAgent(CursorsMixin, ConformingAgent):
    def _cursors_advertised(self) -> bool:
        return False


def main() -> None:
    ForksWithoutCursorsAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-forks-without-cursors").run()


if __name__ == "__main__":
    main()
