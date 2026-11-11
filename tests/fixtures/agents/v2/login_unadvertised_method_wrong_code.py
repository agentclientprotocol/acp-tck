#!/usr/bin/env python3
"""Defect fixture for ACP-AUTH-210 (ADVISORY): advertises one `type: "agent"` method and rejects
`auth/login` for an unadvertised `methodId`, but with `-32000` instead of `-32602`
(authentication.mdx:191). ACP-AUTH-208 (rejection at all) PASSes; the run stays CONFORMANT.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [{"methodId": "tck", "type": "agent", "name": "TCK"}]


class LoginWrongCodeAgent(ConformingAgent):
    def _handle_login(self, msg_id: Any, params: dict[str, Any]) -> None:
        if params.get("methodId") != "tck":
            self._error(msg_id, -32000, "Authentication required")
            return
        super()._handle_login(msg_id, params)


def main() -> None:
    LoginWrongCodeAgent(
        capabilities={"session": {}},
        agent_name="tck-fixture-login-unadvertised-method-wrong-code",
        auth_methods=AUTH_METHODS,
    ).run()


if __name__ == "__main__":
    main()
