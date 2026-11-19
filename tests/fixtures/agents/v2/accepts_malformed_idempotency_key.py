#!/usr/bin/env python3
"""Non-conforming fixture: an `idempotencyKey` that is not a string of 1 to 255 characters (`""`, 256
characters, a number) is treated as omitted and the prompt is inserted, instead of being rejected
with `-32602` (prompt-lifecycle.mdx:441). FAILs `ACP-PROMPT-213` only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AcceptsMalformedIdempotencyKeyAgent(ConformingAgent):
    @staticmethod
    def _key_rejection(key):
        return None


def main() -> None:
    AcceptsMalformedIdempotencyKeyAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-accepts-malformed-idempotency-key"
    ).run()


if __name__ == "__main__":
    main()
