#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.archive` and archives the session, but
leaves a still-hanging `__hang__` turn running instead of cancelling it as `session/close` would.

Only observable with `--cancel-prompt __hang__`; every other prompt finishes normally. FAILs
exactly `ACP-ARCHIVE-201` (the turn never ends, so the TCK's wait times out). The idle-session
rows (`ACP-ARCHIVE-002`..`006`) PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}, "archive": {}}}


class ArchiveDoesNotCancelAgent(ConformingAgent):
    def _close_for_archive(self, session_id: Any) -> None:
        pass


def main() -> None:
    ArchiveDoesNotCancelAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-does-not-cancel"
    ).run()


if __name__ == "__main__":
    main()
