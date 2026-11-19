#!/usr/bin/env python3
"""Non-conforming fixture, for `--cancel-prompt __hang__`: a second request for an `idempotencyKey`
whose prompt is already held while a `__hang__` turn runs is rejected at once with `-32602`
("duplicate key") instead of being answered together with the held one, which the cancel answers
`-32800` (prompt-lifecycle.mdx:453). FAILs `ACP-PROMPT-215` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class HeldRetryRejectedAsDuplicateAgent(ConformingAgent):
    def _prompt_while_busy(self, msg_id: Any, params: dict[str, Any]) -> None:
        key = params.get("idempotencyKey")
        held = self._held_prompts.get(params.get("sessionId"), [])
        if key is not None and any(other.get("idempotencyKey") == key for _, other in held):
            self._error(msg_id, -32602, "Invalid params: duplicate idempotencyKey")
            return
        super()._prompt_while_busy(msg_id, params)


def main() -> None:
    HeldRetryRejectedAsDuplicateAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-held-retry-rejected-as-duplicate"
    ).run()


if __name__ == "__main__":
    main()
