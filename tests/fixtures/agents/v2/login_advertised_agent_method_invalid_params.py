#!/usr/bin/env python3
"""Defect fixture for ACP-AUTH-003: advertises `{"methodId": "tck", "type": "agent"}` but answers
`auth/login` for it with `-32602` (Invalid params), which authentication.mdx:191 reserves for
an id that is not an advertised login method. An unadvertised id is still rejected `-32602`, so
ACP-AUTH-208/210 PASS. Run with `--auth-method tck` and `-k authentication` it FAILs exactly
ACP-AUTH-003.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [{"methodId": "tck", "type": "agent", "name": "TCK"}]


class LoginInvalidParamsAgent(ConformingAgent):
    def _handle_login(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32602, "Invalid params")


def main() -> None:
    LoginInvalidParamsAgent(
        capabilities={"session": {}},
        agent_name="tck-fixture-login-advertised-agent-method-invalid-params",
        auth_methods=AUTH_METHODS,
    ).run()


if __name__ == "__main__":
    main()
