#!/usr/bin/env python3
"""Non-conforming fixture: sends a `state_update` whose `state` is an unrecognized value that
does *not* begin with `_` (`"busy"`), between the running update and the closing idle.

FAILs only `ACP-ENUM-201`. Schema-valid on its own (`StateUpdate`'s `other` fallback branch
accepts any string), so `ACP-SCHEMA-001` does not cascade; the turn still ends normally on the
conforming idle that follows.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnprefixedCustomStateAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._send_update(session_id, {"sessionUpdate": "state_update", "state": "busy"})
        return False  # fire-and-forget: finish the turn immediately, in the same call


def main() -> None:
    UnprefixedCustomStateAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
