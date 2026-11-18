#!/usr/bin/env python3
"""Non-conforming fixture for ACP-AUTH-004 (CAPABILITY, `inferred:authMethods`): otherwise
conforming, advertises a `type: "agent"` auth method but answers `auth/logout` with `-32601`
(Method not found), though an agent advertising `authMethods` MUST implement it
(authentication.mdx:51-52). Run with `--allow-logout` and no `--auth-method`: FAILs exactly
`ACP-AUTH-004` (the standalone path judges only `-32601`); `ACP-AUTH-211` SKIPs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [
    {"methodId": "tck", "type": "agent", "name": "TCK"},
]


class LogoutMethodNotFoundAgent(ConformingAgent):
    def _handle_logout(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32601, "Method not found: auth/logout")


def main() -> None:
    LogoutMethodNotFoundAgent(
        agent_name="tck-fixture-logout-method-not-found",
        auth_methods=AUTH_METHODS,
        capabilities={"session": {}},
    ).run()


if __name__ == "__main__":
    main()
