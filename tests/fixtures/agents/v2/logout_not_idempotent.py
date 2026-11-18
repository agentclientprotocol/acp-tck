#!/usr/bin/env python3
"""Non-conforming fixture for ACP-AUTH-211 (ADVISORY): otherwise conforming, advertises a
`type: "agent"` auth method, but an `auth/logout` with no authenticated state left to end (a
second one right after a successful one) is answered with an error instead of the empty result
(authentication.mdx:273).

Run with `--auth-method tck --allow-logout`: FAILs exactly the ADVISORY `ACP-AUTH-211` (verdict
unaffected); `ACP-AUTH-004` PASSes, since the TCK logs in first and the first logout succeeds.
Without `--auth-method`, `ACP-AUTH-004` SKIPs instead (it would be the standalone path, where
an error other than `-32601` is not judged) and so does `ACP-AUTH-211` (the first logout did
not succeed).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [
    {"methodId": "tck", "type": "agent", "name": "TCK"},
]


class LogoutNotIdempotentAgent(ConformingAgent):
    def _handle_logout(self, msg_id: Any, params: dict[str, Any]) -> None:
        if not self._authenticated:
            self._error(msg_id, -32000, "Authentication required: not logged in")
            return
        super()._handle_logout(msg_id, params)


def main() -> None:
    LogoutNotIdempotentAgent(
        agent_name="tck-fixture-logout-not-idempotent",
        auth_methods=AUTH_METHODS,
        capabilities={"session": {}},
    ).run()


if __name__ == "__main__":
    main()
