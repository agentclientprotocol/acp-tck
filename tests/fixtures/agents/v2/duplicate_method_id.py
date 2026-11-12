#!/usr/bin/env python3
"""A defect fixture for ACP-AUTH-001 (MANDATORY, authentication.mdx:51): advertises two
`authMethods` entries sharing the same `methodId`. Fails ACP-AUTH-001 only, so the run is NOT
CONFORMANT.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [
    {"methodId": "dup", "type": "agent", "name": "First"},
    {"methodId": "dup", "type": "agent", "name": "Second"},
]


def main() -> None:
    ConformingAgent(
        agent_name="tck-fixture-duplicate-method-id",
        auth_methods=AUTH_METHODS,
    ).run()


if __name__ == "__main__":
    main()
