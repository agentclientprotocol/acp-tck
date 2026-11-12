#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive` and implements it, but treats
an `archived` filter value it does not support as `exclude` instead of failing with `-32602`.
Violates ACP-ARCHIVE-004 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import _ARCHIVE_FILTERS, ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class ArchiveFilterFallsBackAgent(ConformingAgent):
    def _handle_list(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("archived") not in _ARCHIVE_FILTERS:
            params = {k: v for k, v in params.items() if k != "archived"}
        super()._handle_list(msg_id, params)


def main() -> None:
    ArchiveFilterFallsBackAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-filter-falls-back"
    ).run()


if __name__ == "__main__":
    main()
