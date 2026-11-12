#!/usr/bin/env python3
"""Non-conforming fixture: rejects unknown and unadvertised prompt content blocks, but with
`-32600` instead of `-32602` (prompt-lifecycle.mdx:313); nothing is inserted. FAILs
`ACP-PROMPT-211` and `ACP-PROMPTCAP-201`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectsContentWithWrongCodeAgent(ConformingAgent):
    def _unsupported_content_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        rejection = super()._unsupported_content_rejection(prompt)
        if rejection is None:
            return None
        return -32600, rejection[1]


def main() -> None:
    RejectsContentWithWrongCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
