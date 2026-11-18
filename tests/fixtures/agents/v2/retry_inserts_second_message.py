#!/usr/bin/env python3
"""Non-conforming fixture: it records an `idempotencyKey` with the message it inserts but never
looks it up, so a retry (the same key, the same or a different prompt) inserts a second message
under a new `messageId` (prompt-lifecycle.mdx:452,457). FAILs `ACP-PROMPT-212` and `ACP-PROMPT-214`
(the reused-key probe inserts too).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RetryInsertsSecondMessageAgent(ConformingAgent):
    def _recorded_message_id(self, session_id, key):
        return None


def main() -> None:
    RetryInsertsSecondMessageAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-retry-inserts-second-message"
    ).run()


if __name__ == "__main__":
    main()
