#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: advertises `sessionCapabilities.close`, but answers
`session/close` for a session it does not (or no longer) know with `-32002` + `data.sessionId`
instead of the empty result. Trips only ACP-CLOSE-003; ACP-CLOSE-001 and the `-32002` checks
for `session/prompt` (ACP-ERROR-003) still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"close": {}}}


class CloseNotIdempotentAgent(ConformingAgent):
    def _handle_close(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions:
            self._unknown_session(msg_id, session_id)
            return
        super()._handle_close(msg_id, params)


def main() -> None:
    CloseNotIdempotentAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-close-not-idempotent").run()


if __name__ == "__main__":
    main()
