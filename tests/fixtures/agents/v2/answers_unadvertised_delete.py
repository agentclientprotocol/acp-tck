#!/usr/bin/env python3
"""Non-conforming fixture: advertises only the `capabilities.session` baseline but still serves
`session/delete` (deleting the session, or succeeding silently for an unknown id) instead of
answering `-32601`, since `capabilities.session.delete` was not advertised.

FAILs exactly `ACP-ERROR-006` (MANDATORY). The `ACP-DELETE-*` rows SKIP as usual: they are gated
on the marker this fixture does not advertise.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersUnadvertisedDeleteAgent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "session/delete":
            self._handle_delete_session(msg_id, params)
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    AnswersUnadvertisedDeleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
