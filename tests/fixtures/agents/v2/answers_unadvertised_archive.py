#!/usr/bin/env python3
"""Non-conforming fixture: advertises only the `capabilities.session` baseline but still serves
`session/archive`/`session/unarchive` instead of answering `-32601`, since
`capabilities.session.archive` was not advertised.

FAILs exactly `ACP-ERROR-006` (MANDATORY). The `ACP-ARCHIVE-*` rows SKIP as usual: they are gated
on the marker this fixture does not advertise.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersUnadvertisedArchiveAgent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method in ("session/archive", "session/unarchive"):
            self._handle_archive_session(msg_id, params, archived=method == "session/archive")
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    AnswersUnadvertisedArchiveAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
