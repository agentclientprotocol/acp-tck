#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.title` and stores a title set with
`session/set_title`, but never sends the `session_info_update` for the change
(session-list.mdx:162, SHOULD). Violates ACP-LIST-208 (ADVISORY) only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SetTitleNoInfoUpdateAgent(ConformingAgent):
    def _notify_title_change(self, session_id: Any, title: str) -> None:
        pass


def main() -> None:
    SetTitleNoInfoUpdateAgent(
        capabilities={"session": {"title": {}}}, agent_name="tck-fixture-set-title-no-info-update"
    ).run()


if __name__ == "__main__":
    main()
