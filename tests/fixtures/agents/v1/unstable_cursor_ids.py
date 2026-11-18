#!/usr/bin/env python3
"""Non-conforming fixture: every `session/load` replays its cursors under fresh `cursorId`s, so the
same position gets a different id on each load. It otherwise behaves like a conforming
cursor-announcing agent. Violates ACP-CURSOR-004 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402

CAPABILITIES = {"loadSession": True, "sessionCapabilities": {"fork": {}}}


class UnstableCursorIdsAgent(CursorsMixin, ConformingAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._load_count = 0
        self._loading = False

    def _handle_load(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._load_count += 1
        self._loading = True
        try:
            super()._handle_load(msg_id, params)
        finally:
            self._loading = False

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        update = params.get("update") if isinstance(params, dict) else None
        if self._loading and isinstance(update, dict) and update.get("sessionUpdate") == "cursor_update":
            update = dict(update, cursorId=f"{update['cursorId']}-load{self._load_count}")
            params = dict(params, update=update)
        super()._notify(method, params)


def main() -> None:
    UnstableCursorIdsAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-unstable-cursor-ids").run()


if __name__ == "__main__":
    main()
