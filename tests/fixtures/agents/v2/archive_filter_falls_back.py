#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive` and implements it, but treats
an `archived` filter value it does not support as `exclude` instead of failing with `-32602`.
FAILs exactly `ACP-ARCHIVE-004`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveFilterFallsBackAgent(ConformingAgent):
    @staticmethod
    def _archive_filter_rejection(archive_filter: Any) -> str | None:
        return None


def main() -> None:
    ArchiveFilterFallsBackAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-filter-falls-back"
    ).run()


if __name__ == "__main__":
    main()
