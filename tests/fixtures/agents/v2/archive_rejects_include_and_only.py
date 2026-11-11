#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive` but rejects the `include` and
`only` `archived` filter values with `-32602`. The Draft RFD (`docs/rfds/session-archive.mdx:112`)
says an agent that advertises `archive` MUST support all three values. FAILs `ACP-ARCHIVE-002`,
`-003` and `-006`, which each need one of those views.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveRejectsIncludeAndOnlyAgent(ConformingAgent):
    @staticmethod
    def _archive_filter_rejection(archive_filter: Any) -> str | None:
        if archive_filter in ("include", "only"):
            return f"unsupported archived filter {archive_filter!r}"
        return ConformingAgent._archive_filter_rejection(archive_filter)


def main() -> None:
    ArchiveRejectsIncludeAndOnlyAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-rejects-include-and-only"
    ).run()


if __name__ == "__main__":
    main()
