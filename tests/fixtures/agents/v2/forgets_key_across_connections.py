#!/usr/bin/env python3
"""Non-conforming fixture: it persists sessions and their message history, so a fresh process
resumes a session and replays its messages, but it keeps `idempotencyKey`s only in memory, so
after a restart a retry of a retained message inserts it again (prompt-lifecycle.mdx:465). FAILs
`ACP-PROMPT-218` only: within one connection the keys work.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ForgetsKeyAcrossConnectionsAgent(ConformingAgent):
    _persist_idempotency_keys = False


def main() -> None:
    ForgetsKeyAcrossConnectionsAgent(
        capabilities={"session": {}},
        persist_sessions=True,
        agent_name="tck-fixture-forgets-key-across-connections",
    ).run()


if __name__ == "__main__":
    main()
