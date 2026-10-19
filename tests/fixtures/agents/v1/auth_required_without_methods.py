#!/usr/bin/env python3
"""Non-conforming fixture: advertises no `authMethods`, yet answers every `session/new` with
`-32000` (authentication required). Trips ACP-AUTH-005; there is no way to authenticate, so
every session-dependent requirement FAILs too.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        agent_name="tck-fixture-auth-required-without-methods", require_auth=True
    ).run()


if __name__ == "__main__":
    main()
