#!/usr/bin/env python3
"""Conforming fixture: advertises `sessionCapabilities.archive`, `list` and `delete`, but lists a
session only after its first prompt (as some real agents do). The archive and delete views cannot
be compared for a fresh session, so ACP-ARCHIVE-002, -003 and -006 SKIP rather than PASS vacuously.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import _ARCHIVE_FILTERS, ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class ArchiveListsNothingUnpromptedAgent(ConformingAgent):
    def _handle_list(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("cursor") is not None:
            self._error(msg_id, -32602, "Invalid params: unknown cursor")
            return
        archived = params.get("archived")
        if archived is not None and archived not in _ARCHIVE_FILTERS:
            self._error(msg_id, -32602, f"Invalid params: unsupported archived filter {archived!r}")
            return
        self._reply(msg_id, {"sessions": []})


def main() -> None:
    ArchiveListsNothingUnpromptedAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-lists-nothing-unprompted"
    ).run()


if __name__ == "__main__":
    main()
