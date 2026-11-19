#!/usr/bin/env python3
"""Non-conforming fixture: a prompt rejected before insertion still records its `idempotencyKey`
(with a `messageId` it never inserted), so the same key with a valid prompt is answered as a retry
with that phantom id and no message is inserted (prompt-lifecycle.mdx:456). FAILs `ACP-PROMPT-219`
only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectedPromptRecordsKeyAgent(ConformingAgent):
    def _after_prompt_rejection(self, session_id: Any, params: dict[str, Any]) -> None:
        self._message_count += 1
        self._record_key(session_id, params.get("idempotencyKey"), f"msg-{self._message_count:04d}")


def main() -> None:
    RejectedPromptRecordsKeyAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-rejected-prompt-records-key"
    ).run()


if __name__ == "__main__":
    main()
