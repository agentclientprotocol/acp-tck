#!/usr/bin/env python3
"""Non-conforming fixture: `idempotencyKey`s are recorded for the whole agent, not per session, so
the same key in another session is answered as a retry of the first session's message instead of
being a new submission (prompt-lifecycle.mdx:461). FAILs `ACP-PROMPT-217` only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class KeyScopedAcrossSessionsAgent(ConformingAgent):
    @staticmethod
    def _key_scope(session_id):
        return "agent"


def main() -> None:
    KeyScopedAcrossSessionsAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-key-scoped-across-sessions"
    ).run()


if __name__ == "__main__":
    main()
