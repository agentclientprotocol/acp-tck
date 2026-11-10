#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive` but rejects the `include` and
`only` `archived` filter values with `-32602`. The Draft RFD (`docs/rfds/session-archive.mdx:112`)
says an agent that advertises `archive` MUST support all three values. Violates ACP-ARCHIVE-002,
-003 and -006, which each need one of those views.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class ArchiveRejectsIncludeAndOnlyAgent(ConformingAgent):
    def _handle_list(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("archived") in ("include", "only"):
            self._error(msg_id, -32602, f"Invalid params: unsupported archived filter {params['archived']!r}")
            return
        super()._handle_list(msg_id, params)


def main() -> None:
    ArchiveRejectsIncludeAndOnlyAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-rejects-include-and-only"
    ).run()


if __name__ == "__main__":
    main()
