#!/usr/bin/env python3
"""Non-conforming fixture: advertises only the `capabilities.session` baseline but still serves
`session/options` instead of answering `-32601`, since `capabilities.session.options` was not
advertised.

FAILs exactly `ACP-ERROR-006` (MANDATORY). The `ACP-OPTIONS-*` rows SKIP as usual: they are gated
on the marker this fixture does not advertise.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AnswersUnadvertisedOptionsAgent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "session/options":
            self._handle_options(msg_id, params)
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    AnswersUnadvertisedOptionsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
