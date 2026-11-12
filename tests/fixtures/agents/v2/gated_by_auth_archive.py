#!/usr/bin/env python3
"""An auth-gated agent that advertises `capabilities.session.archive` and answers `session/new`,
`session/archive` and `session/unarchive` with `-32000` (authentication required) until
`auth/login`. Without `--auth-method`, `ACP-ARCHIVE-005` must SKIP with `AUTH-GATED:` (it creates
a session first) instead of failing on the unexpected `-32000`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class GatedArchiveAgent(ConformingAgent):
    def _handle_archive_session(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        if self._require_auth and not self._authenticated:
            self._error(msg_id, -32000, "Authentication required")
            return
        super()._handle_archive_session(msg_id, params, archived=archived)


def main() -> None:
    GatedArchiveAgent(
        agent_name="tck-fixture-gated-by-auth-archive-v2",
        capabilities={"session": {"archive": {}}},
        auth_methods=[{"methodId": "tck", "type": "agent", "name": "TCK"}],
        require_auth=True,
    ).run()


if __name__ == "__main__":
    main()
