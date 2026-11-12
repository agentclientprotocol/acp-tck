#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive`, but answers
`session/archive`/`session/unarchive` for a session that does not exist with `{}` (the way
`session/delete` does) instead of an error. Violates ACP-ARCHIVE-005 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class ArchiveUnknownSucceedsAgent(ConformingAgent):
    def _handle_archive(self, msg_id: Any, params: dict[str, Any], *, archived: bool) -> None:
        if params.get("sessionId") not in self._sessions:
            self._reply(msg_id, {})
            return
        super()._handle_archive(msg_id, params, archived=archived)


def main() -> None:
    ArchiveUnknownSucceedsAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-unknown-succeeds"
    ).run()


if __name__ == "__main__":
    main()
