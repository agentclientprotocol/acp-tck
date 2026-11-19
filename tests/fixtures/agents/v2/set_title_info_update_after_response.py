#!/usr/bin/env python3
"""Non-conforming fixture: advertises `capabilities.session.title`, stores a title set with
`session/set_title` and sends the `session_info_update` for the change, but after the response
instead of before it (session-list.mdx:163-165 with session-config-options.mdx:392-394, SHOULD).
FAILs exactly `ACP-LIST-209` (ADVISORY); `ACP-LIST-208` PASSes, since the update still arrives
within the quiet drain.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SetTitleInfoUpdateAfterResponseAgent(ConformingAgent):
    _late_title: tuple[Any, str] | None = None

    def _notify_title_change(self, session_id: Any, title: str) -> None:
        self._late_title = (session_id, title)

    def _handle_set_title(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_set_title(msg_id, params)
        if self._late_title is not None:
            session_id, title = self._late_title
            self._late_title = None
            super()._notify_title_change(session_id, title)


def main() -> None:
    SetTitleInfoUpdateAfterResponseAgent(
        capabilities={"session": {"title": {}}},
        agent_name="tck-fixture-set-title-info-update-after-response",
    ).run()


if __name__ == "__main__":
    main()
