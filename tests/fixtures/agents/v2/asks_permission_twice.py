#!/usr/bin/env python3
"""Conforming fixture: sends two overlapping permission requests with distinct ids mid-turn.
Both halves of `ACP-JSONRPC-202` can be observed and PASS (two requests pending at once, no id
reused); nothing else changes from `asks_permission.py`. The turn finishes on the first answer.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class AsksPermissionTwiceAgent(AsksPermissionAgent):
    def _second_permission_id(self) -> Any:
        return self._next_permission_id()

    def _mid_turn_action(self, session_id: Any) -> bool:
        deferred = super()._mid_turn_action(session_id)
        self._send_permission_request(self._second_permission_id(), session_id)
        return deferred


def main() -> None:
    AsksPermissionTwiceAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
